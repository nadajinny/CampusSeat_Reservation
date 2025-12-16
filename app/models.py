from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Enum,
    CheckConstraint,
    Index,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PyEnum

from .database import Base


# ---------------------------------------------------------------------------
# Enum Definitions
# ---------------------------------------------------------------------------
class ReservationStatus(str, PyEnum):
    """예약 상태"""
    RESERVED = "RESERVED"
    IN_USE = "IN_USE"
    CANCELED = "CANCELED"
    COMPLETED = "COMPLETED"


# ---------------------------------------------------------------------------
# User Model (학생 계정)
# ---------------------------------------------------------------------------
class User(Base):
    """
    학생 계정 테이블
    """
    __tablename__ = "users"

    # 학번
    student_id = Column(Integer, primary_key=True, autoincrement=False)

    # 1. timezone=True 추가 (UTC 저장 명시)
    # 2. nullable=True (가입 직후에는 로그인 기록이 없음)
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    reservations = relationship("Reservation", back_populates="user")

    def __repr__(self):
        return f"<User(student_id={self.student_id}, last_login_at={self.last_login_at})>"


# ---------------------------------------------------------------------------
# MeetingRoom Model (회의실 정보)
# ---------------------------------------------------------------------------
class MeetingRoom(Base):
    """
    회의실 정보 테이블
    """
    __tablename__ = "meeting_rooms"

    room_id = Column(Integer, primary_key=True, autoincrement=False)
    min_capacity = Column(Integer, nullable=False, default=3)
    max_capacity = Column(Integer, nullable=False, default=6)
    is_available = Column(Boolean, nullable=False, default=True)

    def __repr__(self):
        return f"<MeetingRoom(room_id={self.room_id}, min={self.min_capacity}, max={self.max_capacity})>"


# ---------------------------------------------------------------------------
# Seat Model (좌석 정보)
# ---------------------------------------------------------------------------
class Seat(Base):
    """
    좌석 정보 테이블
    """
    __tablename__ = "seats"

    seat_id = Column(Integer, primary_key=True, autoincrement=False)
    is_available = Column(Boolean, nullable=False, default=True)

    def __repr__(self):
        return f"<Seat(seat_id={self.seat_id})>"


# ---------------------------------------------------------------------------
# Reservation Model (예약 테이블)
# ---------------------------------------------------------------------------
class Reservation(Base):
    """
    예약 통합 테이블
    """
    __tablename__ = "reservations"

    __table_args__ = (
        CheckConstraint("start_time < end_time", name="check_time_order"),
        CheckConstraint(
            "(meeting_room_id IS NOT NULL AND seat_id IS NULL) OR "
            "(meeting_room_id IS NULL AND seat_id IS NOT NULL)",
            name="check_exclusive_facility"
        ),
        Index('idx_student_start', 'student_id', 'start_time'),
        Index('idx_room_start', 'meeting_room_id', 'start_time', 'status'),
        Index('idx_seat_start', 'seat_id', 'start_time', 'status'),
    )

    reservation_id = Column(Integer, primary_key=True, autoincrement=True)

    student_id = Column(Integer, ForeignKey("users.student_id"), nullable=False)
    meeting_room_id = Column(Integer, ForeignKey("meeting_rooms.room_id"), nullable=True)
    seat_id = Column(Integer, ForeignKey("seats.seat_id"), nullable=True)

    # [수정됨] timezone=True 추가 (UTC 기준 저장)
    start_time = Column(DateTime(timezone=True), nullable=False)
    
    # [수정됨] timezone=True 추가 (UTC 기준 저장)
    end_time = Column(DateTime(timezone=True), nullable=False)

    # [수정됨] timezone=True 추가
    # 주의: SQLite에서는 server_default=func.now()가 UTC 문자열을 잘 생성하는지 확인 필요.
    # 가장 확실한 방법은 CRUD 레벨에서 datetime.now(timezone.utc)를 직접 넣어주는 것입니다.
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    status = Column(
        Enum(ReservationStatus, name="reservation_status_enum"),
        nullable=False,
        default=ReservationStatus.RESERVED
    )

    user = relationship("User", back_populates="reservations")
    meeting_room = relationship("MeetingRoom")
    seat = relationship("Seat")
    participants = relationship("ReservationParticipant", back_populates="reservation")

    def __repr__(self):
        facility = f"room={self.meeting_room_id}" if self.meeting_room_id else f"seat={self.seat_id}"
        return f"<Reservation(id={self.reservation_id}, {facility}, status={self.status})>"


# ---------------------------------------------------------------------------
# ReservationParticipant Model (회의실 참여자)
# ---------------------------------------------------------------------------
class ReservationParticipant(Base):
    """
    회의실 예약 참여자 테이블
    """
    __tablename__ = "reservation_participants"

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    reservation_id = Column(
        Integer,
        ForeignKey("reservations.reservation_id", ondelete="CASCADE"),
        nullable=False
    )
    
    participant_student_id = Column(
        Integer,
        ForeignKey("users.student_id"),
        nullable=False
    )

    reservation = relationship("Reservation", back_populates="participants")

    def __repr__(self):
        return f"<ReservationParticipant(reservation_id={self.reservation_id}, student={self.participant_student_id})>"
    
