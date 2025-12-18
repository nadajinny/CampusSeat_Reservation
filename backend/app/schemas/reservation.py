"""
schemas/reservation.py
"""
from typing import Optional, List
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel, Field, field_serializer

# 한국 시간대(KST) 정의
KST = timezone(timedelta(hours=9))

# -------------------------------------------------------------------
# 1. Base Schema
# -------------------------------------------------------------------
class ReservationBase(BaseModel):
    start_time: datetime = Field(..., description="시작 일시")
    end_time: datetime = Field(..., description="종료 일시")
    status: str = Field("RESERVED", description="예약 상태")

# -------------------------------------------------------------------
# 2. Response Schema (핵심: KST 변환 적용)
# -------------------------------------------------------------------
class ReservationResponse(ReservationBase):
    reservation_id: int = Field(..., description="예약 고유 ID")
    student_id: int = Field(..., description="예약자 학번")
    meeting_room_id: Optional[int] = Field(None, description="회의실 ID")
    seat_id: Optional[int] = Field(None, description="좌석 ID")
    created_at: datetime = Field(..., description="생성 일시")

    model_config = {"from_attributes": True}

    # [핵심] UTC 시간을 한국 시간으로 변환하여 내보내기
    @field_serializer('start_time', 'end_time', 'created_at')
    def serialize_dt(self, dt: datetime, _info):
        if dt is None:
            return None

        # 1. DB에서 꺼낸 시간이 timezone 정보가 없다면 UTC라고 명시
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        # 2. KST(UTC+9)로 변환 후 문자열로 예쁘게 포맷팅
        return dt.astimezone(KST).strftime("%Y-%m-%d %H:%M:%S")


# -------------------------------------------------------------------
# 3. My Reservations List Schema
# -------------------------------------------------------------------
class MyReservationItem(BaseModel):
    """내 예약 목록 아이템 (회의실/좌석 통합)"""

    reservation_id: int = Field(..., description="예약 ID")
    type: str = Field(..., description="예약 유형 (meeting_room | seat)")
    room_id: Optional[int] = Field(None, description="회의실 ID (type=meeting_room일 때)")
    seat_id: Optional[int] = Field(None, description="좌석 ID (type=seat일 때)")
    date: str = Field(..., description="예약 날짜 (YYYY-MM-DD)")
    start_time: str = Field(..., description="시작 시간 (HH:MM)")
    end_time: str = Field(..., description="종료 시간 (HH:MM)")
    status: str = Field(..., description="예약 상태")


class MyReservationsPayload(BaseModel):
    """내 예약 목록 응답"""

    items: List[MyReservationItem] = Field(default_factory=list, description="예약 목록")


# -------------------------------------------------------------------
# 4. Cancel Reservation Response Schema
# -------------------------------------------------------------------
class CancelReservationResponse(BaseModel):
    """예약 취소 응답"""

    reservation_id: int = Field(..., description="예약 ID")
    type: str = Field(..., description="예약 유형 (meeting_room | seat)")
    room_id: Optional[int] = Field(None, description="회의실 ID (type=meeting_room일 때)")
    seat_id: Optional[int] = Field(None, description="좌석 ID (type=seat일 때)")
    status: str = Field(..., description="변경된 상태 (CANCELED)")