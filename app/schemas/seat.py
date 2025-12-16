"""
schemas/seat.py - Seat Schemas
==============================
좌석 관련 스키마 정의 (Validator 추가됨)
"""

from pydantic import BaseModel, Field, field_validator
from ..constants import FacilityConstants


# -------------------------------------------------------------------
# 1. Base Schema (공통 속성)
# -------------------------------------------------------------------
class SeatBase(BaseModel):
    seat_id: int = Field(..., ge=1, description="좌석 번호")
    is_available: bool = Field(True, description="사용 가능 여부")


# -------------------------------------------------------------------
# 2. Request Schemas (생성/수정)
# -------------------------------------------------------------------
class SeatCreate(BaseModel):
    """좌석 생성 요청"""
    seat_id: int = Field(..., ge=1, description="좌석 번호")
    
    @field_validator('seat_id')
    @classmethod
    def check_seat_range(cls, v: int) -> int:
        max_id = FacilityConstants.SEAT_MAX_ID
        if v > max_id:
            raise ValueError(f"좌석 번호는 {max_id}번까지만 존재합니다.")
        return v


# -------------------------------------------------------------------
# 3. Response Schemas (응답)
# -------------------------------------------------------------------
class SeatResponse(SeatBase):
    """좌석 정보 응답 (ORM 매핑 지원)"""
    model_config = {"from_attributes": True}
