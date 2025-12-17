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


class SeatSlotStatus(BaseModel):
    """좌석 슬롯별 가용 상태."""

    start: str = Field(..., description="슬롯 시작 시각 (HH:MM)")
    end: str = Field(..., description="슬롯 종료 시각 (HH:MM)")
    is_available: bool = Field(..., description="예약 가능 여부")


class SeatSeatStatus(BaseModel):
    """좌석 한 개의 전체 슬롯 상태."""

    seat_id: int = Field(..., description="좌석 ID")
    slots: List[SeatSlotStatus] = Field(default_factory=list)


class SeatStatusPayload(BaseModel):
    """좌석 현황 전체 응답 payload."""

    date: str = Field(..., description="조회 날짜")
    operation_hours: TimeRange
    slot_unit_minutes: int = Field(..., description="슬롯 단위(분)")
    seats: List[SeatSeatStatus] = Field(default_factory=list)
