"""
services/reservation_service.py - Reservation persistence helpers.
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app import models


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
    """

    if not include_seats and not include_meeting_rooms:
        return False

    query = db.query(models.Reservation).filter(
        models.Reservation.student_id == student_id,
        models.Reservation.status == models.ReservationStatus.RESERVED,
        models.Reservation.start_time < end_time,
        models.Reservation.end_time > start_time,
    )

    if include_seats and not include_meeting_rooms:
        query = query.filter(models.Reservation.seat_id.isnot(None))
    elif include_meeting_rooms and not include_seats:
        query = query.filter(models.Reservation.meeting_room_id.isnot(None))

    return query.first() is not None


def create_meeting_room_reservation(
    db: Session,
    student_id: int,
    room_id: int,
    start_time: datetime,
    end_time: datetime,
    participant_ids: List[int],
) -> models.Reservation:
    """
    회의실 예약 엔터티를 생성한다.
    """

    reservation = models.Reservation(
        student_id=student_id,
        meeting_room_id=room_id,
        seat_id=None,
        start_time=start_time,
        end_time=end_time,
        status=models.ReservationStatus.RESERVED,
    )
    db.add(reservation)
    db.flush()

    for participant_id in participant_ids:
        participant = models.ReservationParticipant(
            reservation_id=reservation.reservation_id,
            participant_student_id=participant_id,
        )
        db.add(participant)

    db.commit()
    db.refresh(reservation)

    return reservation


def create_seat_reservation(
    db: Session,
    student_id: int,
    seat_id: int,
    start_time: datetime,
    end_time: datetime,
) -> models.Reservation:
    """좌석 예약 레코드를 생성한다."""

    reservation = models.Reservation(
        student_id=student_id,
        meeting_room_id=None,
        seat_id=seat_id,
        start_time=start_time,
        end_time=end_time,
        status=models.ReservationStatus.RESERVED,
    )
    db.add(reservation)
    db.commit()
    db.refresh(reservation)
    return reservation


def get_user_reservations(db: Session, student_id: int) -> List[models.Reservation]:
    """특정 사용자 예약 내역 조회"""

    return (
        db.query(models.Reservation)
        .filter(models.Reservation.student_id == student_id)
        .order_by(models.Reservation.start_time.desc())
        .all()
    )


def cancel_reservation(db: Session, reservation_id: int) -> Optional[models.Reservation]:
    """예약 취소 (상태 변경)"""

    reservation = (
        db.query(models.Reservation)
        .filter(models.Reservation.reservation_id == reservation_id)
        .first()
    )

    if reservation:
        reservation.status = models.ReservationStatus.CANCELED
        db.commit()
        db.refresh(reservation)

    return reservation
