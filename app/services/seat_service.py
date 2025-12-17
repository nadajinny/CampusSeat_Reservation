"""
services/seat_service.py - Seat metadata and reservation helpers.
"""

from datetime import datetime, timedelta, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from app import models
from app.constants import ErrorCode, ReservationLimits
from app.exceptions import (
    BusinessException,
    ConflictException,
    LimitExceededException,
)
from app.schemas.seat import SeatReservationCreate
from app.services import reservation_service, user_service

KST = timezone(timedelta(hours=9))


def get_seat(db: Session, seat_id: int) -> Optional[models.Seat]:
    """좌석 단건 조회"""

    return (
        db.query(models.Seat).filter(models.Seat.seat_id == seat_id).first()
    )


def get_all_seats(db: Session) -> List[models.Seat]:
    """전체 좌석 목록"""

    return db.query(models.Seat).order_by(models.Seat.seat_id).all()


def get_seats_count(db: Session) -> int:
    """좌석 총 개수"""

    return db.query(models.Seat).count()


def create_seat(db: Session, seat_id: int) -> models.Seat:
    """좌석 생성 (중복 체크 포함)"""

    if get_seat(db, seat_id):
        raise ConflictException(
            code=ErrorCode.SEAT_ALREADY_EXISTS,
            message=f"좌석 ID {seat_id}번은 이미 존재합니다.",
        )

    db_seat = models.Seat(seat_id=seat_id, is_available=True)
    db.add(db_seat)
    db.commit()
    db.refresh(db_seat)
    return db_seat


def reserve_seat(
    db: Session,
    student_id: int,
    request: SeatReservationCreate,
) -> models.Reservation:
    """좌석 예약 엔드포인트에서 사용하는 비즈니스 로직."""

    seat = get_seat(db, request.seat_id)
    if seat is None:
        raise BusinessException(
            code=ErrorCode.NOT_FOUND,
            message=f"좌석 ID {request.seat_id}번을 찾을 수 없습니다.",
        )

    start_dt_kst = datetime.combine(request.date, request.start_time, tzinfo=KST)
    end_dt_kst = datetime.combine(request.date, request.end_time, tzinfo=KST)
    start_dt_utc = start_dt_kst.astimezone(timezone.utc)
    end_dt_utc = end_dt_kst.astimezone(timezone.utc)
    duration_minutes = (end_dt_utc - start_dt_utc).total_seconds() / 60

    _ensure_no_seat_conflict(db, request.seat_id, start_dt_utc, end_dt_utc)

    if reservation_service.check_overlap_with_other_facility(
        db,
        student_id,
        start_dt_utc,
        end_dt_utc,
        include_seats=False,
        include_meeting_rooms=True,
    ):
        raise ConflictException(
            code=ErrorCode.OVERLAP_WITH_OTHER_FACILITY,
            message="동일 시간대에 이미 회의실 예약이 존재합니다.",
        )

    used_minutes = _get_daily_seat_usage_minutes(db, student_id, start_dt_kst)
    limit_minutes = ReservationLimits.SEAT_DAILY_LIMIT_MINUTES
    if used_minutes + duration_minutes > limit_minutes:
        raise LimitExceededException(
            code=ErrorCode.DAILY_LIMIT_EXCEEDED,
            message=f"일일 좌석 이용 한도({limit_minutes}분)를 초과했습니다. (현재 {used_minutes}분 이용)",
        )

    user_service.get_or_create_user(db, student_id)
    return reservation_service.create_seat_reservation(
        db=db,
        student_id=student_id,
        seat_id=request.seat_id,
        start_time=start_dt_utc,
        end_time=end_dt_utc,
    )


def _ensure_no_seat_conflict(
    db: Session,
    seat_id: int,
    start_time: datetime,
    end_time: datetime,
) -> None:
    """같은 좌석에서 시간대가 겹치는 예약이 있는지 확인."""

    conflict = (
        db.query(models.Reservation)
        .filter(
            models.Reservation.seat_id == seat_id,
            models.Reservation.status == models.ReservationStatus.RESERVED,
            models.Reservation.start_time < end_time,
            models.Reservation.end_time > start_time,
        )
        .first()
    )

    if conflict:
        raise ConflictException(
            code=ErrorCode.RESERVATION_CONFLICT,
            message="해당 시간대에 이미 좌석 예약이 존재합니다.",
        )


def _get_daily_seat_usage_minutes(
    db: Session,
    student_id: int,
    target_start_kst: datetime,
) -> int:
    """해당 사용자의 일일 좌석 이용량(분)을 계산."""

    start_of_day_kst = target_start_kst.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day_kst = start_of_day_kst + timedelta(hours=23, minutes=59, seconds=59, microseconds=999999)
    start_of_day_utc = start_of_day_kst.astimezone(timezone.utc)
    end_of_day_utc = end_of_day_kst.astimezone(timezone.utc)

    reservations = (
        db.query(models.Reservation)
        .filter(
            models.Reservation.student_id == student_id,
            models.Reservation.seat_id.isnot(None),
            models.Reservation.status == models.ReservationStatus.RESERVED,
            models.Reservation.start_time >= start_of_day_utc,
            models.Reservation.start_time <= end_of_day_utc,
        )
        .all()
    )

    return int(
        sum(
            (reservation.end_time - reservation.start_time).total_seconds() / 60
            for reservation in reservations
        )
    )
