"""
schemas/seat.py - Seat Schemas
==============================
좌석 관련 요청/응답 정의.
"""

from datetime import date as Date, datetime, time as Time
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from app.constants import (
    FacilityConstants,
    OperationHours,
    ReservationLimits,
    ReservationType,
)


class SeatBase(BaseModel):
    """좌석 기본 정보"""

    seat_id: int = Field(..., ge=1, description="좌석 번호")
    is_available: bool = Field(True, description="사용 가능 여부")


class SeatCreate(BaseModel):
    """좌석 생성 요청"""

    seat_id: int = Field(..., ge=1, description="좌석 번호")

    @field_validator("seat_id")
    @classmethod
    def check_seat_range(cls, value: int) -> int:
        max_id = FacilityConstants.SEAT_MAX_ID
        if value > max_id:
            raise ValueError(f"좌석 번호는 {max_id}번까지 생성할 수 있습니다.")
        return value


class SeatReservationCreate(BaseModel):
    """좌석 예약 생성 요청 (직접 선택 또는 랜덤 배정)"""

    date: Date = Field(..., description="예약 날짜 (YYYY-MM-DD)")
    start_time: Time = Field(..., description="시작 시간 (HH:MM)")
    end_time: Time = Field(..., description="종료 시간 (HH:MM)")
    seat_id: Optional[int] = Field(None, ge=1, description="좌석 번호 (랜덤 배정 시 None)")

    @field_validator("date")
    @classmethod
    def validate_date_not_past(cls, value: Date) -> Date:
        """과거 날짜 예약 방지"""
        today = Date.today()
        if value < today:
            raise ValueError("과거 날짜는 예약할 수 없습니다.")
        return value

    @field_validator("seat_id")
    @classmethod
    def validate_seat_id(cls, value: Optional[int]) -> Optional[int]:
        # seat_id가 None이면 랜덤 배정 -> 검증 스킵
        if value is None:
            return value

        # seat_id가 있으면 범위 검증
        if not (FacilityConstants.SEAT_MIN_ID <= value <= FacilityConstants.SEAT_MAX_ID):
            raise ValueError(
                f"좌석 번호는 {FacilityConstants.SEAT_MIN_ID}~{FacilityConstants.SEAT_MAX_ID} 범위여야 합니다."
            )
        return value

    @model_validator(mode="after")
    def validate_time_rules(self):
        start = self.start_time.replace(tzinfo=None)
        end = self.end_time.replace(tzinfo=None)

        if start >= end:
            raise ValueError("종료 시간은 시작 시간보다 늦어야 합니다.")

        op_start = Time(OperationHours.START_HOUR, OperationHours.START_MINUTE)
        op_end = Time(OperationHours.END_HOUR, OperationHours.END_MINUTE)

        if start < op_start or end > op_end:
            raise ValueError("운영 시간(09:00-18:00) 내에서만 예약할 수 있습니다.")

        duration_minutes = (
            datetime.combine(Date.today(), end) - datetime.combine(Date.today(), start)
        ).total_seconds() / 60
        if duration_minutes != ReservationLimits.SEAT_SLOT_MINUTES:
            raise ValueError("좌석 예약은 정확히 2시간 단위로만 가능합니다.")

        # 오늘 날짜인 경우 현재 시간 이후만 예약 가능
        if self.date == Date.today():
            now = datetime.now().time()
            if self.start_time <= now:
                raise ValueError("현재 시간 이후부터 예약할 수 있습니다.")

        return self


class SeatResponse(SeatBase):
    """좌석 정보 응답"""

    model_config = {"from_attributes": True}


class SeatReservationResponse(BaseModel):
    """좌석 예약 응답 페이로드"""

    reservation_id: int = Field(..., description="예약 ID")
    type: str = Field(default=ReservationType.SEAT, description="예약 유형")
    seat_id: int = Field(..., description="좌석 번호")
    date: str = Field(..., description="예약 날짜 (YYYY-MM-DD)")
    start_time: str = Field(..., description="시작 시간 (HH:MM)")
    end_time: str = Field(..., description="종료 시간 (HH:MM)")
    status: str = Field(..., description="예약 상태")
