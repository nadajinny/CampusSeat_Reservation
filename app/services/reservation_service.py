"""
services/reservation_service.py - Reservation persistence helpers.
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import text
from app import models
from app.constants import ErrorCode
from app.exceptions import BusinessException, ForbiddenException

# 충돌 검사용: 해당 시설이 현재 점유 중인지 확인 (예약됨, 사용 중)
CONFLICT_CHECK_STATUSES = [
    models.ReservationStatus.RESERVED,
    models.ReservationStatus.IN_USE,
]


def check_overlap_with_other_facility(
    db: Session,
    student_id: int,
    start_time: datetime,
    end_time: datetime,
    include_seats: bool = True,
    include_meeting_rooms: bool = True,
) -> bool:
    """
    사용자가 동일 시간대에 다른 시설 예약을 가지고 있는지 확인.
    
    검사 범위:
    1. 본인이 예약자(Owner)인 모든 예약 (좌석/회의실)
    2. 본인이 참여자(Participant)로 포함된 예약 (회의실) - [추가됨]
    """

    if not include_seats and not include_meeting_rooms:
        return False

    # ----------------------------------------------------------------
    # 1. [Owner] 내가 예약자(주인)인 경우 확인
    # ----------------------------------------------------------------
    query_owner = db.query(models.Reservation).filter(
        models.Reservation.student_id == student_id,
        models.Reservation.status.in_(CONFLICT_CHECK_STATUSES),
        models.Reservation.start_time < end_time,
        models.Reservation.end_time > start_time,
    )

    if include_seats and not include_meeting_rooms:
        # 좌석만 체크하는 경우
        query_owner = query_owner.filter(models.Reservation.seat_id.isnot(None))
    elif include_meeting_rooms and not include_seats:
        # 회의실만 체크하는 경우
        query_owner = query_owner.filter(models.Reservation.meeting_room_id.isnot(None))
    
    # (둘 다 True면 전체 조회)

    if query_owner.first() is not None:
        return True

    # ----------------------------------------------------------------
    # 2. [Participant] 내가 참여자로 포함된 경우 확인 (회의실 한정)
    # ----------------------------------------------------------------
    # 좌석은 참여자 개념이 없으므로, 회의실을 체크해야 할 때만 수행합니다.
    if include_meeting_rooms:
        query_participant = (
            db.query(models.Reservation)
            .join(
                models.ReservationParticipant,
                models.Reservation.reservation_id == models.ReservationParticipant.reservation_id
            )
            .filter(
                models.ReservationParticipant.participant_student_id == student_id, # 내 학번이 참여자 명단에 있는지
                models.Reservation.status.in_(CONFLICT_CHECK_STATUSES),
                models.Reservation.start_time < end_time,
                models.Reservation.end_time > start_time,
            )
        )
        
        if query_participant.first() is not None:
            return True

    return False


def create_meeting_room_reservation(
    db: Session,
    student_id: int,
    room_id: int,
    start_time: datetime,
    end_time: datetime,
    participant_ids: List[int],
) -> models.Reservation:
    """회의실 예약 엔터티 생성"""
    reservation = models.Reservation(
        student_id=student_id,
        meeting_room_id=room_id,
        seat_id=None,
        start_time=start_time,
        end_time=end_time,
        status=models.ReservationStatus.RESERVED,
    )
    db.add(reservation)
    db.flush() # reservation_id 생성을 위해 flush

    for participant_id in participant_ids:
        participant = models.ReservationParticipant(
            reservation_id=reservation.reservation_id,
            participant_student_id=participant_id,
        )
        db.add(participant)
    
    db.flush()
    return reservation


def create_seat_reservation(
    db: Session,
    student_id: int,
    seat_id: int,
    start_time: datetime,
    end_time: datetime,
) -> models.Reservation:
    """좌석 예약 엔터티 생성"""
    reservation = models.Reservation(
        student_id=student_id,
        meeting_room_id=None,
        seat_id=seat_id,
        start_time=start_time,
        end_time=end_time,
        status=models.ReservationStatus.RESERVED,
    )
    db.add(reservation)
    db.flush()
    
    return reservation


def get_user_reservations(db: Session, student_id: int) -> List[models.Reservation]:
    """
    내 예약 목록 조회 (예약자 + 참여자)
    """
    # 1. 내가 예약한 것
    owned = (
        db.query(models.Reservation)
        .filter(models.Reservation.student_id == student_id)
        .all()
    )

    # 2. 내가 참여자로 포함된 것
    participating = (
        db.query(models.Reservation)
        .join(
            models.ReservationParticipant,
            models.Reservation.reservation_id == models.ReservationParticipant.reservation_id,
        )
        .filter(models.ReservationParticipant.participant_student_id == student_id)
        .all()
    )

    # 병합 및 정렬 (중복 제거)
    merged = {res.reservation_id: res for res in owned + participating}
    return sorted(merged.values(), key=lambda r: r.start_time, reverse=True)


def cancel_reservation(
    db: Session,
    reservation_id: int,
    student_id: int
) -> models.Reservation:
    """예약 취소"""

    try:
        db.execute(text("BEGIN IMMEDIATE"))
        
        reservation = (
            db.query(models.Reservation)
            .filter(models.Reservation.reservation_id == reservation_id)
            .first()
        )

        if not reservation:
            raise BusinessException(
                code=ErrorCode.NOT_FOUND,
                message=f"예약 ID {reservation_id}를 찾을 수 없습니다.",
            )

        if reservation.student_id != student_id:
            raise ForbiddenException(
                code=ErrorCode.AUTH_FORBIDDEN,
                message="본인의 예약만 취소할 수 있습니다.",
            )

        if reservation.status == models.ReservationStatus.CANCELED:
            raise BusinessException(
                code=ErrorCode.RESERVATION_ALREADY_CANCELED,
                message="이미 취소된 예약입니다.",
            )
        
        if reservation.status != models.ReservationStatus.RESERVED:
            raise ForbiddenException(
                code=ErrorCode.AUTH_FORBIDDEN,
                message="예약 중(RESERVED) 상태의 예약만 취소할 수 있습니다.",
            )

        reservation.status = models.ReservationStatus.CANCELED
        db.commit() # [중요] 모든 검증 통과 후 여기서 최종 커밋 (락 해제)
        db.refresh(reservation)

        return reservation

    except Exception as e:
        db.rollback() # [중요] 에러 발생 시 롤백하여 락 해제
        raise e