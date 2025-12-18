"""
api/v1/endpoints/status.py - 시설 현황 엔드포인트
=================================================
Thin Controller 패턴을 적용한 시설 현황 API.
"""

from datetime import date, time

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app import schemas
from app.database import get_db
from app.services import status_service

router = APIRouter(prefix="/status", tags=["Status"])


@router.get(
    "/meeting-rooms",
    response_model=schemas.ApiResponse[schemas.MeetingRoomStatusPayload],
)
def get_meeting_room_status(
    date: date = Query(..., description="조회 날짜 (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
):
    """날짜별 회의실 예약 현황을 조회합니다."""

    payload = status_service.get_meeting_room_status(db, date)
    return schemas.ApiResponse(is_success=True, code=None, payload=payload)


@router.get(
    "/seats",
    response_model=schemas.ApiResponse[schemas.SeatStatusPayload],
)
def get_seat_status(
    date: date = Query(..., description="조회 날짜 (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
):
    """날짜별 좌석 예약 현황을 조회합니다."""

    payload = status_service.get_seat_status(db, date)
    return schemas.ApiResponse(is_success=True, code=None, payload=payload)
