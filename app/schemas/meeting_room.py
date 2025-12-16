"""
schemas/meeting_room.py - Meeting Room Schemas
==============================================
회의실 정보 및 예약 요청 스키마
"""

from typing import List, Self
from datetime import date as Date, time as Time, datetime, timedelta
from pydantic import BaseModel, Field, model_validator

from ..constants import OperationHours, ReservationLimits

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
class ParticipantBase(BaseModel):
    """참여자 정보"""
    student_id: int = Field(..., description="참여자 학번")


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
        min_length=3, 
        description="참여자 목록 (최소 3명)"
    )
    
    @model_validator(mode='after')
    def check_time_rules(self) -> Self:
        """
        예약 시간 관련 비즈니스 규칙 검증
        1. 종료 시간이 시작 시간보다 늦어야 함
        2. 운영 시간(09:00~18:00) 내여야 함
        3. 예약 단위가 정확히 1시간이어야 함
        """
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