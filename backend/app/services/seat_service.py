"""
services/seat_service.py - Seat metadata and reservation helpers.
"""

from datetime import datetime, timedelta, timezone
from typing import List, Optional

from sqlalchemy import and_, func, select, text
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

# 충돌 검사용: 해당 좌석이 현재 점유 중인지 확인
CONFLICT_CHECK_STATUSES = [
    models.ReservationStatus.RESERVED,
    models.ReservationStatus.IN_USE,
]

# 한도 계산용: 당일 총 사용량 계산 (완료된 것도 포함)
USAGE_COUNT_STATUSES = [
    models.ReservationStatus.RESERVED,
    models.ReservationStatus.IN_USE,
    models.ReservationStatus.COMPLETED,
]


def get_seat(db: Session, seat_id: int) -> Optional[models.Seat]:
    """좌석 단건 조회"""
    return db.query(models.Seat).filter(models.Seat.seat_id == seat_id).first()


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
    """
    좌석 예약 비즈니스 로직 (동시성 제어 적용).
    
    핵심 변경사항:
    - SELECT ... FOR UPDATE를 사용하여 조회 시점에 Row Lock을 획득합니다.
    - 트랜잭션이 커밋(create_seat_reservation 내부)될 때까지 락이 유지됩니다.
    """
    try:
        # [핵심] 로직 시작하자마자 '쓰기 잠금' 획득
        # 이후의 모든 조회(SELECT)와 생성(INSERT)은 이 락 안에서 보호됨
        db.execute(text("BEGIN IMMEDIATE"))

        # 시간 변환 (공통)
        start_dt_kst = datetime.combine(request.date, request.start_time, tzinfo=KST)
        end_dt_kst = datetime.combine(request.date, request.end_time, tzinfo=KST)
        start_dt_utc = start_dt_kst.astimezone(timezone.utc)
        end_dt_utc = end_dt_kst.astimezone(timezone.utc)
        duration_minutes = (end_dt_utc - start_dt_utc).total_seconds() / 60

        selected_seat_id = None
        # -------------------------------------------------------
        # 1. 좌석 결정 및 Lock 획득 (Critical Section)
        # -------------------------------------------------------
        if request.seat_id is not None:
            seat = (
                db.query(models.Seat)
                .filter(models.Seat.seat_id == request.seat_id)
                .first()
            )

            if not seat.is_available:
                raise BusinessException(
                    code=ErrorCode.SEAT_NOT_AVAILABLE,
                    message=f"좌석 ID {request.seat_id}번은 현재 이용 불가 상태입니다.",
                )
            
            selected_seat_id = seat.seat_id

            # Lock을 획득한 상태에서 시간 충돌 여부를 확실하게 검증합니다.
            _ensure_no_seat_conflict(db, selected_seat_id, start_dt_utc, end_dt_utc)

        else:
            # [랜덤 배정 모드]
            # 가용 좌석 중 하나를 찾아 가져옵니다.
            selected_seat_id = _find_and_lock_random_available_seat(
                db, start_dt_utc, end_dt_utc
            )
            
            if selected_seat_id is None:
                raise ConflictException(
                    code=ErrorCode.RESERVATION_CONFLICT,
                    message="해당 시간대에 예약 가능한 좌석이 없습니다.",
                )

        # -------------------------------------------------------
        # 2. 비즈니스 로직 검증 (사용자 중복, 한도 등)
        # -------------------------------------------------------
        
        # 본인의 다른 좌석 예약과 시간 충돌 확인
        if reservation_service.check_overlap_with_other_facility(
            db,
            student_id,
            start_dt_utc,
            end_dt_utc,
            include_seats=True,
            include_meeting_rooms=False,
        ):
            raise ConflictException(
                code=ErrorCode.OVERLAP_WITH_OTHER_FACILITY,
                message="동일 시간대에 이미 좌석 예약이 존재합니다.",
            )

        # 회의실 예약과 시간 충돌 확인
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

        # 일일 이용 한도 확인
        used_minutes = _get_daily_seat_usage_minutes(db, student_id, start_dt_kst)
        limit_minutes = ReservationLimits.SEAT_DAILY_LIMIT_MINUTES
        if used_minutes + duration_minutes > limit_minutes:
            raise LimitExceededException(
                code=ErrorCode.DAILY_LIMIT_EXCEEDED,
                message=f"일일 좌석 이용 한도({limit_minutes}분)를 초과했습니다. (현재 {used_minutes}분 이용)",
            )

        # 사용자 정보 확인 및 생성
        user_service.get_or_create_user(db, student_id)
        
        reservation = reservation_service.create_seat_reservation(
            db=db,
            student_id=student_id,
            seat_id=selected_seat_id,
            start_time=start_dt_utc,
            end_time=end_dt_utc,
        )

        # -------------------------------------------------------
        # 3. 예약 생성 (여기서 Commit 되면서 Lock 해제됨)
        # -------------------------------------------------------
        db.commit()
        db.refresh(reservation)
        return reservation
    except Exception as e:
        db.rollback()
        raise e


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
            models.Reservation.status.in_(CONFLICT_CHECK_STATUSES),
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
            models.Reservation.status.in_(USAGE_COUNT_STATUSES),
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


def _find_and_lock_random_available_seat(
    db: Session,
    start_time: datetime,
    end_time: datetime,
) -> Optional[int]:
    """
    DB 쿼리 한 번으로 예약 가능한 좌석을 찾아 Lock을 걸고 반환합니다.
    (동시성 문제 해결 + 성능 최적화)
    """
    
    # 1. 해당 시간대에 이미 예약된 좌석 ID들을 찾는 서브쿼리
    occupied_subquery = (
        select(models.Reservation.seat_id)
        .where(
            models.Reservation.seat_id.isnot(None),
            models.Reservation.status.in_(CONFLICT_CHECK_STATUSES),
            models.Reservation.end_time > start_time,
            models.Reservation.start_time < end_time,
        )
    )

    # 2. 예약되지 않은(is_available=True) 좌석 중 하나를 랜덤으로 선택하여 Lock
    # func.random(): PostgreSQL, SQLite / func.rand(): MySQL
    # 사용 환경에 따라 다를 수 있으나 보통 func.random()이 표준에 가깝습니다.
    stmt = (
        db.query(models.Seat.seat_id)
        .filter(models.Seat.is_available.is_(True))
        .filter(models.Seat.seat_id.notin_(occupied_subquery))
        .order_by(func.random())  # DB 랜덤 정렬
        .limit(1)
    )
    
    result = stmt.first()
    
    return result[0] if result else None
