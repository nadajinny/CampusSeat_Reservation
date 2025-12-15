"""
crud.py - Database Operations (CRUD Functions)
===============================================
This module contains pure functions for database operations.

CRUD stands for:
- Create: Add new records to the database
- Read: Retrieve records from the database
- Update: Modify existing records
- Delete: Remove records from the database

Key Concepts for Students:
- These are pure functions, NOT classes
- Each function takes a database session as the first argument
- Functions are simple and do one thing well
- This keeps the code easy to understand and test

Why pure functions instead of classes?
- Simpler to understand for beginners
- No need to manage object state
- Easier to test in isolation
- Clear input -> output relationship
"""

from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from . import models, schemas


# ---------------------------------------------------------------------------
# READ Operations
# ---------------------------------------------------------------------------

def get_seat(db: Session, seat_id: int) -> models.Seat | None:
    """
    Get a single seat by its ID.

    Args:
        db: Database session
        seat_id: The ID of the seat to find

    Returns:
        Seat object if found, None if not found

    Example:
        seat = get_seat(db, seat_id=1)
        if seat:
            print(f"Found seat {seat.seat_id}")
        else:
            print("Seat not found")
    """
    return db.query(models.Seat).filter(models.Seat.seat_id == seat_id).first()


def get_all_seats(db: Session) -> list[models.Seat]:
    """
    Get all seats from the database.

    Args:
        db: Database session

    Returns:
        List of all Seat objects, ordered by seat_id

    Example:
        seats = get_all_seats(db)
        for seat in seats:
            print(f"Seat {seat.seat_id}: active={seat.is_active}")
    """
    return db.query(models.Seat).order_by(models.Seat.seat_id).all()


def get_seats_count(db: Session) -> int:
    """
    Count the total number of seats in the database.

    Args:
        db: Database session

    Returns:
        Total count of seats

    Example:
        count = get_seats_count(db)
        print(f"Total seats: {count}")
    """
    return db.query(models.Seat).count()


# ---------------------------------------------------------------------------
# CREATE Operations
# ---------------------------------------------------------------------------

def create_seat(db: Session, seat: schemas.SeatCreate) -> models.Seat:
    """
    Create a new seat in the database.

    Args:
        db: Database session
        seat: SeatCreate schema with seat data

    Returns:
        The newly created Seat object

    Example:
        new_seat = SeatCreate(seat_id=1, is_active=True)
        created = create_seat(db, new_seat)
        print(f"Created seat with ID: {created.seat_id}")

    Process:
        1. Create a SQLAlchemy model instance from Pydantic data
        2. Add it to the session (staged for insert)
        3. Commit the transaction (actually write to DB)
        4. Refresh to get any DB-generated values
        5. Return the created object
    """
    # Create SQLAlchemy model instance
    # model_dump() converts Pydantic model to dictionary
    db_seat = models.Seat(**seat.model_dump())

    # Add to session (staged, not yet in DB)
    db.add(db_seat)

    # Commit transaction (write to DB)
    db.commit()

    # Refresh to get the latest data from DB
    db.refresh(db_seat)

    return db_seat


# ---------------------------------------------------------------------------
# Meeting Room Reservation Operations
# ---------------------------------------------------------------------------

def check_room_conflict(
    db: Session,
    room_id: int,
    start_time: datetime
) -> bool:
    """
    회의실 중복 예약 확인

    Args:
        db: 데이터베이스 세션
        room_id: 회의실 ID (1-3)
        start_time: 시작 시간

    Returns:
        충돌이 있으면 True, 없으면 False
    """
    conflict = db.query(models.Reservation).filter(
        models.Reservation.meeting_room_id == room_id,
        models.Reservation.start_time == start_time,
        models.Reservation.status == models.ReservationStatus.RESERVED
    ).first()

    return conflict is not None


def check_user_daily_meeting_limit(
    db: Session,
    student_id: int,
    target_date: datetime
) -> int:
    """
    사용자의 해당 날짜 회의실 예약 총 시간(분) 계산

    Args:
        db: 데이터베이스 세션
        student_id: 학번
        target_date: 대상 날짜

    Returns:
        총 예약 시간(분) - 제한: 120분 = 2시간
    """
    start_of_day = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)

    reservations = db.query(models.Reservation).filter(
        models.Reservation.student_id == student_id,
        models.Reservation.meeting_room_id.isnot(None),  # 회의실만
        models.Reservation.status == models.ReservationStatus.RESERVED,
        models.Reservation.start_time >= start_of_day,
        models.Reservation.start_time <= end_of_day
    ).all()

    total_minutes = sum(
        (r.end_time - r.start_time).total_seconds() / 60
        for r in reservations
    )

    return int(total_minutes)


def check_user_weekly_meeting_limit(
    db: Session,
    student_id: int,
    target_date: datetime
) -> int:
    """
    사용자의 해당 주 회의실 예약 총 시간(분) 계산

    Args:
        db: 데이터베이스 세션
        student_id: 학번
        target_date: 대상 주의 임의 날짜

    Returns:
        총 예약 시간(분) - 제한: 300분 = 5시간
    """
    # 해당 주의 월요일 계산
    start_of_week = target_date - timedelta(days=target_date.weekday())
    start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)

    # 해당 주의 일요일 계산
    end_of_week = start_of_week + timedelta(days=6, hours=23, minutes=59, seconds=59)

    reservations = db.query(models.Reservation).filter(
        models.Reservation.student_id == student_id,
        models.Reservation.meeting_room_id.isnot(None),  # 회의실만
        models.Reservation.status == models.ReservationStatus.RESERVED,
        models.Reservation.start_time >= start_of_week,
        models.Reservation.start_time <= end_of_week
    ).all()

    total_minutes = sum(
        (r.end_time - r.start_time).total_seconds() / 60
        for r in reservations
    )

    return int(total_minutes)


def check_overlap_with_other_facility(
    db: Session,
    student_id: int,
    start_time: datetime
) -> bool:
    """
    동일 시간에 다른 시설 예약이 있는지 확인

    Args:
        db: 데이터베이스 세션
        student_id: 학번
        start_time: 확인할 시작 시간

    Returns:
        겹치는 예약이 있으면 True, 없으면 False
    """
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
    participants: list
) -> models.Reservation:
    """
    회의실 예약 생성

    Args:
        db: 데이터베이스 세션
        student_id: 예약자 학번
        room_id: 회의실 ID (1-3)
        start_time: 시작 시간
        end_time: 종료 시간
        participants: 참여자 목록 [{"student_id": "...", "name": "..."}]

    Returns:
        생성된 Reservation 객체

    처리 과정:
        1. 사용자가 DB에 없으면 생성 (upsert)
        2. 예약 레코드 생성
        3. 참여자 레코드 생성
        4. 트랜잭션 커밋
    """
    # 1. User 존재 확인 및 생성 (upsert)
    user = db.query(models.User).filter(models.User.student_id == student_id).first()
    if not user:
        user = models.User(student_id=student_id)
        db.add(user)
        db.flush()

    # 2. Reservation 생성
    reservation = models.Reservation(
        student_id=student_id,
        meeting_room_id=room_id,
        seat_id=None,
        start_time=start_time,
        end_time=end_time,
        is_owner=True,
        status=models.ReservationStatus.RESERVED
    )
    db.add(reservation)
    db.flush()  # reservation_id 획득

    # 3. Participants 생성
    for p in participants:
        participant = models.ReservationParticipant(
            reservation_id=reservation.reservation_id,
            participant_student_id=int(p.get("student_id")) if p.get("student_id") else None,
            participant_name=p.get("name")
        )
        db.add(participant)

    # 4. 커밋
    db.commit()
    db.refresh(reservation)

    return reservation
