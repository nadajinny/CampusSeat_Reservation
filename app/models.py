"""
models.py - SQLAlchemy Database Models
======================================
This module defines the database tables using SQLAlchemy ORM.

Key Concepts for Students:
- Each class represents a table in the database
- Each attribute represents a column in the table
- SQLAlchemy automatically handles the mapping between Python objects and SQL

ERD Overview:
- users: 학생 계정 (studentID, name, department, role)
- meeting_rooms: 회의실 정보 (roomID 1~3)
- seats: 좌석 정보 (seatID 1~70)
- reservations: 예약 통합 테이블
"""

from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy.sql import func
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Enum,
    CheckConstraint,
)
from sqlalchemy.orm import relationship

from .database import Base


# ---------------------------------------------------------------------------
# Enum Definitions
# ---------------------------------------------------------------------------
class UserRole(str, PyEnum):
    """사용자 역할"""
    STUDENT = "student"
    ADMIN = "admin"


class ReservationStatus(str, PyEnum):
    """예약 상태"""
    RESERVED = "RESERVED"      # 예약 완료
    IN_USE = "IN_USE"          # 사용 중
    CANCELED = "CANCELED"      # 취소됨
    COMPLETED = "COMPLETED"    # 이용 완료


# ---------------------------------------------------------------------------
# User Model (학생 계정)
# ---------------------------------------------------------------------------
class User(Base):
    """
    학생 계정 테이블

    Columns:
        student_id: 학번 (PK)
        name: 학생 이름
        department: 소속 학과
        role: 권한 구분 (student, admin)
    """

    __tablename__ = "users"

    # 학번 - Primary Key
    student_id = Column(Integer, primary_key=True, autoincrement=False)

    # 학생 이름
    name = Column(String(50), nullable=True)

    # 소속 학과
    department = Column(String(100), nullable=True)

    # 권한 구분 (student, admin)
    role = Column(
        Enum(UserRole, name="user_roles_enum"),
        nullable=False,
        default=UserRole.STUDENT
    )

    # ---------------------------------------------------------------------------
    # Relationships
    # ---------------------------------------------------------------------------
    reservations = relationship("Reservation", back_populates="user")

    def __repr__(self):
        return f"<User(student_id={self.student_id}, name={self.name}, role={self.role})>"


# ---------------------------------------------------------------------------
# MeetingRoom Model (회의실 정보)
# ---------------------------------------------------------------------------
class MeetingRoom(Base):
    """
    회의실 정보 테이블

    Columns:
        room_id: 회의실 번호 (1~3) (PK)
        min_capacity: 최소 이용 인원 (기본 3명)
        max_capacity: 최대 이용 인원

    초기 데이터(seed):
        (1, 3, NULL), (2, 3, NULL), (3, 3, NULL)
    """

    __tablename__ = "meeting_rooms"

    # 회의실 번호 (1~3)
    room_id = Column(Integer, primary_key=True, autoincrement=False)

    # 최소 이용 인원 (기본 3명)
    min_capacity = Column(Integer, nullable=False, default=3)

    # 최대 이용 인원
    max_capacity = Column(Integer, nullable=True)

    def __repr__(self):
        return f"<MeetingRoom(room_id={self.room_id}, min={self.min_capacity}, max={self.max_capacity})>"


# ---------------------------------------------------------------------------
# Seat Model (좌석 정보)
# ---------------------------------------------------------------------------
class Seat(Base):
    """
    좌석 정보 테이블

    Columns:
        seat_id: 좌석 번호 (1~70) (PK)

    초기 데이터(seed):
        1~70 insert
    """

    __tablename__ = "seats"

    # 좌석 번호 (1~70)
    seat_id = Column(Integer, primary_key=True, autoincrement=False)

    def __repr__(self):
        return f"<Seat(seat_id={self.seat_id})>"


# ---------------------------------------------------------------------------
# Reservation Model (예약 테이블)
# ---------------------------------------------------------------------------
class Reservation(Base):
    """
    예약 통합 테이블

    회의실과 좌석 예약을 하나의 테이블로 관리합니다.
    meeting_room_id와 seat_id 중 하나만 값이 있어야 합니다.

    Columns:
        reservation_id: 예약 고유 ID (PK, 자동 증가)
        student_id: 예약자 학번 (FK → users)
        meeting_room_id: 회의실 번호 (FK → meeting_rooms), 회의실 예약 시
        seat_id: 좌석 번호 (FK → seats), 좌석 예약 시
        start_time: 시작 시간
        end_time: 종료 시간
        is_owner: 예약 생성자 여부
        created_at: 생성 일시
        status: 예약 상태 (RESERVED, IN_USE, CANCELED, COMPLETED)

    Check Constraints:
        - start_time < end_time
        - meeting_room_id와 seat_id 중 하나만 NOT NULL
    """

    __tablename__ = "reservations"

    # ---------------------------------------------------------------------------
    # Check Constraints (데이터 무결성 보장)
    # ---------------------------------------------------------------------------
    __table_args__ = (
        # 시작 시간이 종료 시간보다 앞서야 함
        CheckConstraint("start_time < end_time", name="check_time_order"),

        # meeting_room_id와 seat_id 중 하나만 NOT NULL (XOR 조건)
        CheckConstraint(
            "(meeting_room_id IS NOT NULL AND seat_id IS NULL) OR "
            "(meeting_room_id IS NULL AND seat_id IS NOT NULL)",
            name="check_exclusive_facility"
        ),
    )

    # ---------------------------------------------------------------------------
    # Column Definitions
    # ---------------------------------------------------------------------------

    # 예약 고유 ID (자동 증가)
    reservation_id = Column(Integer, primary_key=True, autoincrement=True)

    # 예약자 학번 (FK → users)
    student_id = Column(
        Integer,
        ForeignKey("users.student_id"),
        nullable=False
    )

    # 회의실 번호 (FK → meeting_rooms), 회의실 예약 시에만 사용
    meeting_room_id = Column(
        Integer,
        ForeignKey("meeting_rooms.room_id"),
        nullable=True
    )

    # 좌석 번호 (FK → seats), 좌석 예약 시에만 사용
    seat_id = Column(
        Integer,
        ForeignKey("seats.seat_id"),
        nullable=True
    )

    # 시작 시간
    start_time = Column(DateTime, nullable=False)

    # 종료 시간
    end_time = Column(DateTime, nullable=False)

    # 예약 생성자 여부
    is_owner = Column(Boolean, nullable=False, default=True)

    # 생성 일시
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    # 예약 상태: RESERVED, IN_USE, CANCELED, COMPLETED
    status = Column(
        Enum(ReservationStatus, name="reservation_status_enum"),
        nullable=False,
        default=ReservationStatus.RESERVED
    )

    # ---------------------------------------------------------------------------
    # Relationships
    # ---------------------------------------------------------------------------
    # 예약자
    user = relationship("User", back_populates="reservations")

    # 회의실
    meeting_room = relationship("MeetingRoom")

    # 좌석
    seat = relationship("Seat")

    def __repr__(self):
        facility = f"room={self.meeting_room_id}" if self.meeting_room_id else f"seat={self.seat_id}"
        return f"<Reservation(id={self.reservation_id}, {facility}, status={self.status})>"
    