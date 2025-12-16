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
    LoginSuccessResponse,
    LoginErrorResponse,
)

# Seat
from .seat import SeatCreate, SeatResponse

# Meeting Room
from .meeting_room import (
    MeetingRoomResponse,
    MeetingRoomReservationCreate,
    ParticipantBase,
)

# Reservation
from .reservation import ReservationResponse, ReservationBase

__all__ = [
    "ApiResponse",
    "ErrorPayload",
    "LoginRequest",
    "TokenPayload",
    "UserResponse",
    "LoginSuccessResponse",
    "LoginErrorResponse",
    "SeatCreate",
    "SeatResponse",
    "MeetingRoomResponse",
    "MeetingRoomReservationCreate",
    "ParticipantBase",
    "ReservationResponse",
    "ReservationBase",
]