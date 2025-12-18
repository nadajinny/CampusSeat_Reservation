"""
services/seat_service.py - Seat metadata and reservation helpers.
"""

import random
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
    """좌석 예약 비즈니스 로직 (직접 선택 또는 랜덤 배정)."""

    # 시간 변환 (공통)
    start_dt_kst = datetime.combine(request.date, request.start_time, tzinfo=KST)
    end_dt_kst = datetime.combine(request.date, request.end_time, tzinfo=KST)
    start_dt_utc = start_dt_kst.astimezone(timezone.utc)
    end_dt_utc = end_dt_kst.astimezone(timezone.utc)
    duration_minutes = (end_dt_utc - start_dt_utc).total_seconds() / 60

    # 1. 좌석 결정 (직접 선택 vs 랜덤 배정)
    if request.seat_id is not None:
        # 직접 선택 모드: 좌석 존재 확인
        seat = get_seat(db, request.seat_id)
        if seat is None:
            raise BusinessException(
                code=ErrorCode.NOT_FOUND,
                message=f"좌석 ID {request.seat_id}번을 찾을 수 없습니다.",
            )
        selected_seat_id = request.seat_id
    else:
        # 랜덤 배정 모드: 가용 좌석 중 랜덤 선택
        selected_seat_id = _find_random_available_seat(db, start_dt_utc, end_dt_utc)
        if selected_seat_id is None:
            raise ConflictException(
                code=ErrorCode.RESERVATION_CONFLICT,
                message="해당 시간대에 예약 가능한 좌석이 없습니다.",
            )

    # 2. 해당 좌석 중복 확인
    _ensure_no_seat_conflict(db, selected_seat_id, start_dt_utc, end_dt_utc)

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
        seat_id=selected_seat_id,  # 직접 선택 또는 랜덤 배정된 seat_id
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


def _find_random_available_seat(
    db: Session,
    start_time: datetime,
    end_time: datetime,
) -> Optional[int]:
    """
    주어진 시간대에 예약 가능한 좌석 중 하나를 랜덤으로 선택.

    Args:
        db: 데이터베이스 세션
        start_time: 예약 시작 시간 (UTC)
        end_time: 예약 종료 시간 (UTC)

    Returns:
        선택된 seat_id 또는 None (가용 좌석이 없는 경우)
    """
    from app.constants import FacilityConstants

    # 1. 전체 좌석 ID 목록 (1~70)
    all_seat_ids = list(range(
        FacilityConstants.SEAT_MIN_ID,
        FacilityConstants.SEAT_MAX_ID + 1
    ))

    # 2. 해당 시간대에 예약된 좌석 조회
    occupied_seats = (
        db.query(models.Reservation.seat_id)
        .filter(
            models.Reservation.seat_id.isnot(None),
            models.Reservation.status == models.ReservationStatus.RESERVED,
            models.Reservation.start_time < end_time,
            models.Reservation.end_time > start_time,
        )
        .all()
    )

    occupied_seat_ids = {row[0] for row in occupied_seats if row[0] is not None}

    # 3. 가용 좌석 = 전체 - 예약됨
    available_seat_ids = [sid for sid in all_seat_ids if sid not in occupied_seat_ids]

    # 4. 랜덤 선택
    if not available_seat_ids:
        return None

    return random.choice(available_seat_ids)
