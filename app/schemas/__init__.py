"""
schemas package
===============
Pydantic 스키마 모듈
"""

# Common
from .common import ApiResponse, ErrorPayload

# User
from .user import (
    LoginRequest,
    TokenPayload,
    UserResponse,
)

# Seat
from .seat import (
    SeatCreate,
    SeatReservationCreate,
    SeatReservationResponse,
    SeatResponse,
)

# Meeting Room
from .meeting_room import (
    MeetingRoomResponse,
    MeetingRoomReservationCreate,
    ParticipantBase,
)

# Reservation
from .reservation import (
    ReservationResponse,
    ReservationBase,
    MyReservationItem,
    MyReservationsPayload,
    CancelReservationResponse,
)

# Status
from .status import (
    TimeRange,
    MeetingRoomSlotStatus,
    MeetingRoomRoomStatus,
    MeetingRoomStatusPayload,
    SeatSlotStatus,
    SeatSeatStatus,
    SeatStatusPayload,
)
__all__ = [
    "ApiResponse",
    "ErrorPayload",
    "LoginRequest",
    "TokenPayload",
    "UserResponse",
    "SeatCreate",
    "SeatResponse",
    "SeatReservationCreate",
    "SeatReservationResponse",
    "MeetingRoomResponse",
    "MeetingRoomReservationCreate",
    "ParticipantBase",
    "ReservationResponse",
    "ReservationBase",
    "MyReservationItem",
    "MyReservationsPayload",
    "CancelReservationResponse",
    "TimeRange",
    "MeetingRoomSlotStatus",
    "MeetingRoomRoomStatus",
    "MeetingRoomStatusPayload",
    "SeatSlotStatus",
    "SeatSeatStatus",
    "SeatStatusPayload",
]
