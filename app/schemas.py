"""
schemas.py - Pydantic Models for Request/Response Validation
============================================================
This module defines Pydantic models for data validation and serialization.

Key Concepts for Students:
- Pydantic models validate incoming data (requests)
- They also define the shape of outgoing data (responses)
- They are different from SQLAlchemy models:
    - SQLAlchemy models = Database tables
    - Pydantic models = API request/response format

Why use Pydantic?
- Automatic data validation (type checking)
- Automatic error messages for invalid data
- Clear documentation in Swagger UI
- Easy serialization to/from JSON
"""

from typing import Optional, Any, List, Union
from datetime import date as Date, time as Time
from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Common API Response Format
# ---------------------------------------------------------------------------

class ApiResponse(BaseModel):
    """
    공통 API 응답 포맷

    모든 API 응답은 이 포맷을 따릅니다.

    성공 시:
        {
            "is_success": true,
            "code": null,
            "payload": { ... }
        }

    실패 시:
        {
            "is_success": false,
            "code": "ERROR_CODE",
            "payload": { "message": "..." }
        }
    """
    is_success: bool = Field(..., description="요청 성공 여부")
    code: Optional[str] = Field(None, description="에러 코드 (성공 시 null)")
    payload: Any = Field(..., description="응답 데이터 또는 에러 상세")


# ---------------------------------------------------------------------------
# Request Schemas (for receiving data from clients)
# ---------------------------------------------------------------------------

class SeatCreate(BaseModel):
    """
    Schema for creating a new seat.

    Used when: POST /seats/

    Example request body:
        {
            "seat_id": 1
        }
    """

    # seat_id is required, must be >= 1
    seat_id: int = Field(..., ge=1, description="Unique seat identifier (must be >= 1)")


# ---------------------------------------------------------------------------
# Response Schemas (for sending data to clients)
# ---------------------------------------------------------------------------

class SeatResponse(BaseModel):
    """
    Schema for seat data in API responses.

    Used when: Returning seat data to the client

    Example response:
        {
            "seat_id": 1
        }
    """

    seat_id: int = Field(..., description="Unique seat identifier")

    # ---------------------------------------------------------------------------
    # Pydantic Configuration
    # ---------------------------------------------------------------------------
    model_config = {
        # from_attributes=True allows Pydantic to read data from SQLAlchemy models
        # This is needed because SQLAlchemy models use attributes, not dict keys
        #
        # Without this: SeatResponse(**seat.__dict__)  # Doesn't work well
        # With this:    SeatResponse.model_validate(seat)  # Works perfectly!
        "from_attributes": True
    }


# ---------------------------------------------------------------------------
# Meeting Room Reservation Schemas
# ---------------------------------------------------------------------------

class ParticipantBase(BaseModel):
    """
    회의실 예약 참여자 정보

    학번 또는 이름 중 최소 하나는 제공되어야 합니다.
    """
    student_id: Optional[str] = Field(None, description="학번 (9자리)")
    name: Optional[str] = Field(None, description="참여자 이름")


class MeetingRoomReservationCreate(BaseModel):
    """
    회의실 예약 생성 요청

    검증:
    - room_id: 1-3 범위
    - date: YYYY-MM-DD 형식
    - start_time, end_time: HH:MM 형식
    - participants: 최소 3명
    """
    room_id: int = Field(..., ge=1, le=3, description="회의실 ID (1-3)")
    date: Date = Field(..., description="예약 날짜 (YYYY-MM-DD)")
    start_time: Time = Field(..., description="시작 시간 (HH:MM)")
    end_time: Time = Field(..., description="종료 시간 (HH:MM)")
    participants: List[ParticipantBase] = Field(
        ...,
        min_length=3,
        description="참여자 목록 (최소 3명)"
    )


class MeetingRoomReservationResponse(BaseModel):
    """
    회의실 예약 응답

    예약 생성 성공 시 반환되는 데이터
    """
    reservation_id: int = Field(..., description="예약 ID")
    meeting_room_id: int = Field(..., description="회의실 ID")
    date: Date = Field(..., description="예약 날짜")
    start_time: Time = Field(..., description="시작 시간")
    end_time: Time = Field(..., description="종료 시간")
    status: str = Field(..., description="예약 상태 (RESERVED)")

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Authentication Schemas
# ---------------------------------------------------------------------------


class LoginRequest(BaseModel):
    """
    Schema for login requests.

    Accepts 9-digit student IDs as string or integer.
    """

    student_id: str = Field(
        ...,
        description="9-digit student ID used as login credential (string or number)",
        examples=["202312345"],
    )

    @field_validator("student_id", mode="before")
    @classmethod
    def normalize_student_id(cls, value: str | int) -> str:
        """
        Accept either string or integer input and normalize to stripped string.
        Actual validation happens in the router so we can control errors.
        """

        if isinstance(value, int):
            return str(value)
        if isinstance(value, str):
            return value.strip()
        raise TypeError("student_id must be a string or integer")


class TokenPayload(BaseModel):
    """Payload returned when authentication succeeds."""

    access_token: str = Field(..., description="Opaque access token")
    student_id: int = Field(..., description="Authenticated student ID")


class ErrorPayload(BaseModel):
    """Payload shape for error responses."""

    message: str


class LoginSuccessResponse(BaseModel):
    """Response body for successful login attempts."""

    is_success: bool = Field(default=True, description="Indicates the request succeeded")
    code: Optional[str] = Field(default=None, description="Optional application code")
    payload: TokenPayload


class LoginErrorResponse(BaseModel):
    """Response body for failed login attempts."""

    is_success: bool = Field(default=False, description="Indicates the request failed")
    code: str = Field(..., description="Application-specific error code")
    payload: ErrorPayload


LoginResponse = Union[LoginSuccessResponse, LoginErrorResponse]
