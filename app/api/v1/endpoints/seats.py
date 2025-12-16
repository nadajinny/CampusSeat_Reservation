"""
api/v1/endpoints/seats.py - Seat Endpoints
==========================================
좌석 관련 API 엔드포인트

이 라우터는 Thin Controller 패턴을 따릅니다:
- HTTP 요청/응답 처리 및 ApiResponse 포맷팅 담당
- 비즈니스 로직은 Service 계층에 위임
"""

from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ....database import get_db
from ....schemas import seat as seat_schemas
from ....schemas.common import ApiResponse
from ....services import seat_service
from ....exceptions import BusinessException

router = APIRouter(prefix="/seats", tags=["Seats"])


@router.post("", response_model=ApiResponse[seat_schemas.SeatResponse], status_code=status.HTTP_201_CREATED)
def create_seat(
    seat: seat_schemas.SeatCreate,
    db: Session = Depends(get_db)
):
    """
    좌석 생성
    """
    try:
        # 서비스 호출 (Pydantic 모델을 풀어서 순수 데이터로 전달)
        new_seat = seat_service.create_seat(db=db, seat_id=seat.seat_id)
        
        return ApiResponse(
            is_success=True,
            code=None,
            payload=new_seat
        )
    except BusinessException as e:
        return ApiResponse(
            is_success=False,
            code=e.code,
            payload={"message": e.message}
        )


@router.get("", response_model=ApiResponse[List[seat_schemas.SeatResponse]])
def read_seats(db: Session = Depends(get_db)):
    """
    전체 좌석 조회
    """
    seats = seat_service.get_all_seats(db)
    return ApiResponse(
        is_success=True,
        code=None,
        payload=seats
    )


@router.get("/{seat_id}", response_model=ApiResponse[seat_schemas.SeatResponse])
def read_seat(
    seat_id: int,
    db: Session = Depends(get_db)
):
    """
    특정 좌석 조회
    """
    seat = seat_service.get_seat(db, seat_id=seat_id)
    if seat is None:
        return ApiResponse(
            is_success=False,
            code="NOT_FOUND",
            payload={"message": f"Seat with id {seat_id} not found"}
        )
    
    return ApiResponse(
        is_success=True,
        code=None,
        payload=seat
    )