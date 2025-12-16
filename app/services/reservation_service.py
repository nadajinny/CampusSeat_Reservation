"""
services/reservation_service.py - Reservation Service
=====================================================
예약 엔티티(Reservation)에 대한 순수 CRUD 및 공통 로직
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session

from .. import models


def check_overlap_with_other_facility(
    db: Session,
    student_id: int,
    start_time: datetime
) -> bool:
    """동일 시간에 다른 시설(회의실/좌석) 예약이 있는지 확인"""
    overlap = db.query(models.Reservation).filter(
        models.Reservation.student_id == student_id,
        models.Reservation.status == models.ReservationStatus.RESERVED,
        models.Reservation.start_time == start_time
    ).first()

    return overlap is not None


def create_meeting_room_reservation(
    db: Session,
    student_id: int,
    room_id: int,
    start_time: datetime,
    end_time: datetime,
    participant_ids: List[int]
) -> models.Reservation:
    """
    회의실 예약 데이터 생성 (순수 DB Insert)
    """
    # 1. 예약 객체 생성
    reservation = models.Reservation(
        student_id=student_id,
        meeting_room_id=room_id,
        seat_id=None,
        start_time=start_time,
        end_time=end_time,
        status=models.ReservationStatus.RESERVED
    )
    db.add(reservation)
    db.flush()

    # 2. 참여자 데이터 생성
    for p_id in participant_ids:
        participant = models.ReservationParticipant(
            reservation_id=reservation.reservation_id,
            participant_student_id=p_id
        )
        db.add(participant)

    db.commit()
    db.refresh(reservation)

    return reservation


def get_user_reservations(db: Session, student_id: int) -> List[models.Reservation]:
    """특정 사용자의 예약 목록 조회"""
    return db.query(models.Reservation).filter(
        models.Reservation.student_id == student_id
    ).order_by(models.Reservation.start_time.desc()).all()


def cancel_reservation(db: Session, reservation_id: int) -> Optional[models.Reservation]:
    """예약 취소 (상태 변경)"""
    reservation = db.query(models.Reservation).filter(
        models.Reservation.reservation_id == reservation_id
    ).first()

    if reservation:
        reservation.status = models.ReservationStatus.CANCELED
        db.commit()
        db.refresh(reservation)

    return reservation