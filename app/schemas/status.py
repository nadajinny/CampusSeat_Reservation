"""
schemas/status.py - Status/Availability Schemas
================================================
Pydantic models for read-only facility availability endpoints.
"""

from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class TimeRange(BaseModel):
    """공통 시간 범위 표현."""

    start: str = Field(..., description="시작 시각 (HH:MM)")
    end: str = Field(..., description="종료 시각 (HH:MM)")


class MeetingRoomSlotStatus(BaseModel):
    """회의실 슬롯별 가용 상태."""

    start: str = Field(..., description="슬롯 시작 시각 (HH:MM)")
    end: str = Field(..., description="슬롯 종료 시각 (HH:MM)")
    is_available: bool = Field(..., description="예약 가능 여부")


class MeetingRoomRoomStatus(BaseModel):
    """회의실 한 개의 전체 슬롯 상태."""

    room_id: int = Field(..., description="회의실 ID")
    slots: List[MeetingRoomSlotStatus] = Field(default_factory=list)


class MeetingRoomStatusPayload(BaseModel):
    """회의실 현황 전체 응답 payload."""

    date: str = Field(..., description="조회 날짜")
    operation_hours: TimeRange
    slot_unit_minutes: int = Field(..., description="슬롯 단위(분)")
    rooms: List[MeetingRoomRoomStatus] = Field(default_factory=list)


class SeatAvailabilityPayload(BaseModel):
    """특정 시간 범위의 좌석 가용 정보."""

    date: str = Field(..., description="조회 날짜")
    time_range: TimeRange
    total_seats: int = Field(..., description="전체 좌석 수")
    available_seat_ids: List[int] = Field(default_factory=list)
    available_count: int = Field(..., description="가용 좌석 수")


class SeatSlotStatus(BaseModel):
    """2시간 슬롯 가용 여부."""

    start: str = Field(..., description="슬롯 시작 시각")
    end: str = Field(..., description="슬롯 종료 시각")
    has_available_seat: bool = Field(..., description="빈 좌석 존재 여부")


class SeatSlotsPayload(BaseModel):
    """슬롯 단위 좌석 현황."""

    date: str = Field(..., description="조회 날짜")
    slot_unit_minutes: int = Field(..., description="슬롯 단위(분)")
    slots: List[SeatSlotStatus] = Field(default_factory=list)
