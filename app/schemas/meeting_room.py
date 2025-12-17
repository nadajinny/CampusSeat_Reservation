"""
schemas/meeting_room.py - Meeting Room Schemas
==============================================
회의실 정보 및 예약 요청 스키마
"""

from typing import List, Self
from datetime import date as Date, time as Time, datetime, timedelta
from pydantic import BaseModel, Field, model_validator, field_validator

from app.constants import OperationHours, ReservationLimits
from app.schemas.user import UserBase

# -------------------------------------------------------------------
# 1. Meeting Room Entity Schemas
# -------------------------------------------------------------------
class MeetingRoomBase(BaseModel):
    room_id: int = Field(..., ge=1, le=3, description="회의실 ID (1-3)")
    min_capacity: int = Field(3, description="최소 수용 인원")
    max_capacity: int = Field(6, description="최대 수용 인원")
    is_available: bool = Field(True, description="사용 가능 여부")


class MeetingRoomResponse(MeetingRoomBase):
    """회의실 정보 응답"""
    model_config = {"from_attributes": True}


# -------------------------------------------------------------------
# 2. Reservation Request Schemas (예약 생성 전용)
# -------------------------------------------------------------------
class ParticipantBase(UserBase):
    """참여자 정보"""
    pass


class MeetingRoomReservationCreate(BaseModel):
    """
    회의실 예약 요청
    - 입력 편의를 위해 Date와 Time을 분리해서 받음
    - 서비스 계층에서 datetime으로 합쳐질 예정
    """
    room_id: int = Field(..., ge=1, le=3, description="회의실 ID")
    date: Date = Field(..., description="예약 날짜 (YYYY-MM-DD)")
    start_time: Time = Field(..., description="시작 시간 (HH:MM)")
    end_time: Time = Field(..., description="종료 시간 (HH:MM)")
    participants: List[ParticipantBase] = Field(
        ...,
        description="참여자 목록 (최소 3명)",
    )
    
    # ---------------------------------------------------------
    # [NEW] 참여자 중복 검증 (필드 검증)
    # ---------------------------------------------------------
    @field_validator('participants')
    @classmethod
    def check_unique_participants(cls, v: List[ParticipantBase]) -> List[ParticipantBase]:
        """
        참여자 목록 내 중복 학번 검사
        예: [202312345, 202312345, 202312345] -> Error
        """
        # 입력된 객체 리스트에서 student_id만 추출
        ids = [p.student_id for p in v]
        
        # Set으로 변환하여 중복 제거 후 길이 비교
        if len(set(ids)) != len(ids):
            raise ValueError("참여자 목록에 중복된 학번이 존재합니다.")
            
        return v
    
    # ---------------------------------------------------------
    # 시간 규칙 검증 (기존 로직 유지)
    # ---------------------------------------------------------
    @model_validator(mode='after')
    def check_time_rules(self) -> Self:
        # [KST 직접 수신 방식]
        # 들어온 시간에 Timezone 정보가 있으면(Z 등), 과감히 떼버리고 그 숫자를 KST로 인정
        # 예: 14:00Z가 들어오면 -> 14:00 (KST)로 해석 (클라이언트가 실수로 Z 붙였다고 가정)
        
        if self.start_time.tzinfo is not None:
            self.start_time = self.start_time.replace(tzinfo=None)
        
        if self.end_time.tzinfo is not None:
            self.end_time = self.end_time.replace(tzinfo=None)

        # 이제 start, end는 무조건 "입력한 숫자 그대로"의 시간입니다.
        # 즉, 14:00으로 들어왔으면 14:00 KST로 간주하고 바로 검증합니다.
        
        start = self.start_time
        end = self.end_time

        # 1. 시간 순서 확인
        if start >= end:
            raise ValueError("종료 시간은 시작 시간보다 이후여야 합니다.")

        # 2. 운영 시간 확인
        op_start = Time(OperationHours.START_HOUR, OperationHours.START_MINUTE)
        op_end = Time(OperationHours.END_HOUR, OperationHours.END_MINUTE)

        if start < op_start or end > op_end:
            raise ValueError(f"운영 시간({op_start.strftime('%H:%M')} ~ {op_end.strftime('%H:%M')}) 내에서만 예약 가능합니다.")

        # 3. 1시간 단위 확인
        # Time 객체끼리는 빼기가 안 되므로 datetime으로 변환 후 계산
        dummy_date = Date.today()
        dt_start = datetime.combine(dummy_date, start)
        dt_end = datetime.combine(dummy_date, end)
        
        duration = (dt_end - dt_start).total_seconds() / 60
        
        if duration != ReservationLimits.MEETING_ROOM_SLOT_MINUTES:
            raise ValueError(f"회의실은 {ReservationLimits.MEETING_ROOM_SLOT_MINUTES}분(1시간) 단위로만 예약 가능합니다.")

        return self
