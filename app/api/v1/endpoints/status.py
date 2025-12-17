"""
api/v1/endpoints/status.py - 시설 현황 엔드포인트
=================================================
회의실·좌석 가용 현황 관련 API 엔드포인트.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
from typing import Iterable

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ....database import get_db
from .... import constants, models, schemas

router = APIRouter(prefix="/status", tags=["Status"])

ACTIVE_RESERVATION_STATUSES: tuple[models.ReservationStatus, ...] = (
    models.ReservationStatus.RESERVED,
    models.ReservationStatus.IN_USE,
)
KST = timezone(timedelta(hours=9))


@router.get(
    "/meeting-rooms",
    response_model=schemas.ApiResponse[schemas.MeetingRoomStatusPayload],
)
def get_meeting_room_status(
    date: date = Query(..., description="조회 날짜 (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
):
    """
    날짜별 회의실 예약 현황을 조회합니다.
    """

    slot_minutes = constants.ReservationLimits.MEETING_ROOM_SLOT_MINUTES
    slots = _generate_daily_slots(date, slot_minutes)
    day_start_local, day_end_local = _day_bounds(date)
    day_start = _to_utc(day_start_local)
    day_end = _to_utc(day_end_local)

    reservations = (
        db.query(models.Reservation)
        .filter(
            models.Reservation.meeting_room_id.isnot(None),
            models.Reservation.start_time >= day_start,
            models.Reservation.start_time < day_end,
            models.Reservation.status.in_(ACTIVE_RESERVATION_STATUSES),
        )
        .all()
    )
    reservations_by_room = defaultdict(list)
    for reservation in reservations:
        if reservation.meeting_room_id is not None:
            reservations_by_room[reservation.meeting_room_id].append(reservation)

    now_utc = datetime.now(timezone.utc)
    room_payloads: list[schemas.MeetingRoomRoomStatus] = []
    for room_id in constants.FacilityConstants.MEETING_ROOM_IDS:
        slot_payloads = []
        for slot_start, slot_end in slots:
            is_available = False
            slot_start_utc = _to_utc(slot_start)
            slot_end_utc = _to_utc(slot_end)
            if slot_end_utc > now_utc:
                is_available = True
                for res in reservations_by_room.get(room_id, []):
                    res_start = _ensure_utc(res.start_time)
                    res_end = _ensure_utc(res.end_time)
                    if _overlaps(res_start, res_end, slot_start_utc, slot_end_utc):
                        is_available = False
                        break
            slot_payloads.append(
                schemas.MeetingRoomSlotStatus(
                    start=_format_time(slot_start),
                    end=_format_time(slot_end),
                    is_available=is_available,
                )
            )
        room_payloads.append(
            schemas.MeetingRoomRoomStatus(room_id=room_id, slots=slot_payloads)
        )

    payload = schemas.MeetingRoomStatusPayload(
        date=date.isoformat(),
        operation_hours=schemas.TimeRange(
            start=_operation_start_str(), end=_operation_end_str()
        ),
        slot_unit_minutes=slot_minutes,
        rooms=room_payloads,
    )
    return schemas.ApiResponse(is_success=True, code=None, payload=payload)


@router.get(
    "/seats",
    response_model=schemas.ApiResponse[schemas.SeatAvailabilityPayload],
)
def get_seat_availability(
    date: date = Query(..., description="조회 날짜 (YYYY-MM-DD)"),
    start_time: time = Query(..., description="시작 시각 (HH:MM)"),
    end_time: time = Query(..., description="종료 시각 (HH:MM)"),
    db: Session = Depends(get_db),
):
    """특정 시간대에 예약 가능한 좌석을 조회합니다."""

    start_dt_local, end_dt_local = _build_time_range(date, start_time, end_time)
    start_dt = _to_utc(start_dt_local)
    end_dt = _to_utc(end_dt_local)
    seat_ids = _all_seat_ids()

    occupied_seats = _query_occupied_seats(db, start_dt, end_dt)
    available_seats = [sid for sid in seat_ids if sid not in occupied_seats]

    payload = schemas.SeatAvailabilityPayload(
        date=date.isoformat(),
        time_range=schemas.TimeRange(
            start=_format_time(start_dt_local), end=_format_time(end_dt_local)
        ),
        total_seats=len(seat_ids),
        available_seat_ids=available_seats,
        available_count=len(available_seats),
    )
    return schemas.ApiResponse(is_success=True, code=None, payload=payload)


@router.get(
    "/seats/slots",
    response_model=schemas.ApiResponse[schemas.SeatSlotsPayload],
)
def get_seat_slot_status(
    date: date = Query(..., description="조회 날짜 (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
):
    """날짜별 좌석 2시간 슬롯 가용 여부를 조회합니다."""

    slot_minutes = constants.ReservationLimits.SEAT_SLOT_MINUTES
    slots = _generate_daily_slots(date, slot_minutes)
    seat_ids = _all_seat_ids()
    total_seats = len(seat_ids)
    day_start_local, day_end_local = _day_bounds(date)
    day_start = _to_utc(day_start_local)
    day_end = _to_utc(day_end_local)

    reservations = (
        db.query(models.Reservation)
        .filter(
            models.Reservation.seat_id.isnot(None),
            models.Reservation.status.in_(ACTIVE_RESERVATION_STATUSES),
            models.Reservation.start_time < day_end,
            models.Reservation.end_time > day_start,
        )
        .all()
    )

    slot_payloads: list[schemas.SeatSlotStatus] = []
    now_utc = datetime.now(timezone.utc)
    for slot_start, slot_end in slots:
        slot_start_utc = _to_utc(slot_start)
        slot_end_utc = _to_utc(slot_end)
        if slot_end_utc <= now_utc:
            has_available = False
        else:
            occupied = {
                res.seat_id
                for res in reservations
                if res.seat_id is not None
                and _overlaps(
                    _ensure_utc(res.start_time),
                    _ensure_utc(res.end_time),
                    slot_start_utc,
                    slot_end_utc,
                )
            }
            has_available = len(occupied) < total_seats
        slot_payloads.append(
            schemas.SeatSlotStatus(
                start=_format_time(slot_start),
                end=_format_time(slot_end),
                has_available_seat=has_available,
            )
        )

    payload = schemas.SeatSlotsPayload(
        date=date.isoformat(),
        slot_unit_minutes=slot_minutes,
        slots=slot_payloads,
    )
    return schemas.ApiResponse(is_success=True, code=None, payload=payload)


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------


def _build_time_range(target_date: date, start: time, end: time) -> tuple[datetime, datetime]:
    if start >= end:
        raise HTTPException(
            status_code=400,
            detail="시작 시각이 종료 시각보다 클 수 없습니다.",
        )
    if start < _operation_start() or end > _operation_end():
        raise HTTPException(
            status_code=400,
            detail="운영 시간(09:00-18:00)을 벗어났습니다.",
        )
    start_dt = datetime.combine(target_date, start, tzinfo=KST)
    end_dt = datetime.combine(target_date, end, tzinfo=KST)
    now = datetime.now(KST)
    if end_dt <= now:
        raise HTTPException(
            status_code=400,
            detail="이미 지난 시간대는 조회할 수 없습니다.",
        )
    return start_dt, end_dt


def _generate_daily_slots(target_date: date, slot_minutes: int) -> list[tuple[datetime, datetime]]:
    start_dt = datetime.combine(target_date, _operation_start(), tzinfo=KST)
    end_dt = datetime.combine(target_date, _operation_end(), tzinfo=KST)
    delta = timedelta(minutes=slot_minutes)
    slots: list[tuple[datetime, datetime]] = []
    cursor = start_dt
    while cursor < end_dt:
        slot_end = cursor + delta
        slots.append((cursor, slot_end))
        cursor = slot_end
    return slots


def _overlaps(a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime) -> bool:
    return a_start < b_end and a_end > b_start


def _format_time(value: datetime | time) -> str:
    if isinstance(value, datetime):
        value = value.time()
    return value.strftime("%H:%M")


def _operation_start() -> time:
    return time(constants.OperationHours.START_HOUR, constants.OperationHours.START_MINUTE)


def _operation_end() -> time:
    return time(constants.OperationHours.END_HOUR, constants.OperationHours.END_MINUTE)


def _operation_start_str() -> str:
    return _format_time(_operation_start())


def _operation_end_str() -> str:
    return _format_time(_operation_end())


def _day_bounds(target_date: date) -> tuple[datetime, datetime]:
    return (
        datetime.combine(target_date, _operation_start(), tzinfo=KST),
        datetime.combine(target_date, _operation_end(), tzinfo=KST),
    )


def _all_seat_ids() -> list[int]:
    return list(
        range(
            constants.FacilityConstants.SEAT_MIN_ID,
            constants.FacilityConstants.SEAT_MAX_ID + 1,
        )
    )


def _query_occupied_seats(db: Session, start_dt: datetime, end_dt: datetime) -> set[int]:
    rows: Iterable[tuple[int]] = (
        db.query(models.Reservation.seat_id)
        .filter(
            models.Reservation.seat_id.isnot(None),
            models.Reservation.status.in_(ACTIVE_RESERVATION_STATUSES),
            models.Reservation.start_time < end_dt,
            models.Reservation.end_time > start_dt,
        )
        .all()
    )
    return {row[0] for row in rows if row[0] is not None}


def _to_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=KST)
    else:
        dt = dt.astimezone(KST)
    return dt.astimezone(timezone.utc)


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)
