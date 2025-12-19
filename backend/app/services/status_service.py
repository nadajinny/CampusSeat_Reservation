"""
services/status_service.py - Status query helpers.
"""

from datetime import date, time as Time, datetime, timezone, timedelta
from typing import List

from sqlalchemy.orm import Session

from app import models, schemas
from app.constants import FacilityConstants, OperationHours, ReservationLimits, SeatSlotConstants

KST = timezone(timedelta(hours=9))
CONFLICT_CHECK_STATUSES = [
    models.ReservationStatus.RESERVED,
    models.ReservationStatus.IN_USE,
]


def get_meeting_room_status(
    db: Session,
    target_date: date
) -> schemas.MeetingRoomStatusPayload:
    """
    회의실 예약 현황 조회 (날짜별, 슬롯별)
    """
    # 1. 운영 시간 정보
    operation_hours = schemas.TimeRange(
        start=f"{OperationHours.START_HOUR:02d}:{OperationHours.START_MINUTE:02d}",
        end=f"{OperationHours.END_HOUR:02d}:{OperationHours.END_MINUTE:02d}",
    )

    # 2. 1시간 단위 슬롯 생성 (09:00-18:00)
    slots_time = []
    current_hour = OperationHours.START_HOUR
    while current_hour < OperationHours.END_HOUR:
        start = Time(current_hour, 0)
        end = Time(current_hour + 1, 0)
        slots_time.append((start, end))
        current_hour += 1

    # 3. 각 회의실별로 슬롯 상태 생성
    rooms = []
    for room_id in FacilityConstants.MEETING_ROOM_IDS:
        room_slots = []

        for start_time, end_time in slots_time:
            # KST 시간을 UTC로 변환
            start_dt_kst = datetime.combine(target_date, start_time, tzinfo=KST)
            end_dt_kst = datetime.combine(target_date, end_time, tzinfo=KST)
            start_dt_utc = start_dt_kst.astimezone(timezone.utc)
            end_dt_utc = end_dt_kst.astimezone(timezone.utc)

            # 해당 시간대에 예약이 있는지 확인
            conflict = db.query(models.Reservation).filter(
                models.Reservation.meeting_room_id == room_id,
                models.Reservation.status.in_(CONFLICT_CHECK_STATUSES),
                models.Reservation.start_time < end_dt_utc,
                models.Reservation.end_time > start_dt_utc,
            ).first()

            room_slots.append(schemas.MeetingRoomSlotStatus(
                start=start_time.strftime("%H:%M"),
                end=end_time.strftime("%H:%M"),
                is_available=(conflict is None),
            ))

        rooms.append(schemas.MeetingRoomRoomStatus(
            room_id=room_id,
            slots=room_slots,
        ))

    return schemas.MeetingRoomStatusPayload(
        date=target_date.isoformat(),
        operation_hours=operation_hours,
        slot_unit_minutes=ReservationLimits.MEETING_ROOM_SLOT_MINUTES,
        rooms=rooms,
    )


def get_seat_status(
    db: Session,
    target_date: date
) -> schemas.SeatStatusPayload:
    """
    좌석 예약 현황 조회 (날짜별, 슬롯별)
    """
    # 1. 운영 시간 정보
    operation_hours = schemas.TimeRange(
        start=f"{OperationHours.START_HOUR:02d}:{OperationHours.START_MINUTE:02d}",
        end=f"{OperationHours.END_HOUR:02d}:{OperationHours.END_MINUTE:02d}",
    )

    # 2. 권장 슬롯 사용 (09-11, 10-12, 11-13, 12-14, 13-15, 14-16, 15-17, 16-18)
    slots_time = []
    for start_str, end_str in SeatSlotConstants.RECOMMENDED_SLOTS:
        start_hour, start_minute = map(int, start_str.split(":"))
        end_hour, end_minute = map(int, end_str.split(":"))
        start = Time(start_hour, start_minute)
        end = Time(end_hour, end_minute)
        slots_time.append((start, end))

    # 3. 각 좌석별로 슬롯 상태 생성
    seats = []
    for seat_id in range(FacilityConstants.SEAT_MIN_ID, FacilityConstants.SEAT_MAX_ID + 1):
        seat_slots = []

        for start_time, end_time in slots_time:
            # KST 시간을 UTC로 변환
            start_dt_kst = datetime.combine(target_date, start_time, tzinfo=KST)
            end_dt_kst = datetime.combine(target_date, end_time, tzinfo=KST)
            start_dt_utc = start_dt_kst.astimezone(timezone.utc)
            end_dt_utc = end_dt_kst.astimezone(timezone.utc)

            # 해당 시간대에 예약이 있는지 확인
            conflict = db.query(models.Reservation).filter(
                models.Reservation.seat_id == seat_id,
                models.Reservation.status.in_(CONFLICT_CHECK_STATUSES),
                models.Reservation.start_time < end_dt_utc,
                models.Reservation.end_time > start_dt_utc,
            ).first()

            seat_slots.append(schemas.SeatSlotStatus(
                start=start_time.strftime("%H:%M"),
                end=end_time.strftime("%H:%M"),
                is_available=(conflict is None),
            ))

        seats.append(schemas.SeatSeatStatus(
            seat_id=seat_id,
            slots=seat_slots,
        ))

    return schemas.SeatStatusPayload(
        date=target_date.isoformat(),
        operation_hours=operation_hours,
        slot_unit_minutes=ReservationLimits.SEAT_SLOT_MINUTES,
        seats=seats,
    )
