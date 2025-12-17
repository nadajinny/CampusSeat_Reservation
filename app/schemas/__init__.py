"""
schemas package
===============
Pydantic 스키마 모듈
"""

# Common
from .common import ApiResponse, ErrorPayload, ErrorResponseModel

# User
from .user import (
    LoginRequest,
    TokenPayload,
    UserResponse,
    LoginSuccessResponse,
    LoginErrorResponse,
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
from .reservation import ReservationResponse, ReservationBase

# Status
from .status import (
    TimeRange,
    MeetingRoomSlotStatus,
    MeetingRoomRoomStatus,
    MeetingRoomStatusPayload,
    SeatAvailabilityPayload,
    SeatSlotStatus,
    SeatSlotsPayload,
)
__all__ = [
    "ApiResponse",
    "ErrorPayload",
    "ErrorResponseModel",
    "LoginRequest",
    "TokenPayload",
    "UserResponse",
    "LoginSuccessResponse",
    "LoginErrorResponse",
    "SeatCreate",
    "SeatResponse",
    "SeatReservationCreate",
    "SeatReservationResponse",
    "MeetingRoomResponse",
    "MeetingRoomReservationCreate",
    "ParticipantBase",
    "ReservationResponse",
    "ReservationBase",
    "TimeRange",
    "MeetingRoomSlotStatus",
    "MeetingRoomRoomStatus",
    "MeetingRoomStatusPayload",
    "SeatAvailabilityPayload",
    "SeatSlotStatus",
    "SeatSlotsPayload",
]
