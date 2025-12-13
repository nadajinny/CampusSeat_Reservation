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

from typing import Optional, Any
from pydantic import BaseModel, Field


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
            "seat_id": 1,
            "is_active": true
        }
    """

    # seat_id is required, must be >= 1
    seat_id: int = Field(..., ge=1, description="Unique seat identifier (must be >= 1)")

    # is_active is optional, defaults to True
    is_active: bool = Field(default=True, description="Whether the seat is active")


# ---------------------------------------------------------------------------
# Response Schemas (for sending data to clients)
# ---------------------------------------------------------------------------

class SeatResponse(BaseModel):
    """
    Schema for seat data in API responses.

    Used when: Returning seat data to the client

    Example response:
        {
            "seat_id": 1,
            "is_active": true
        }
    """

    seat_id: int = Field(..., description="Unique seat identifier")
    is_active: bool = Field(..., description="Whether the seat is active")

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
