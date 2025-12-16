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

from app.database import get_db
from app import schemas
from app.schemas.common import ApiResponse
from app.services import seat_service
from app.exceptions import BusinessException
from app.constants import ErrorCode
# app/api/docs.py에 NOT_FOUND가 정의되어 있다고 가정합니다.
# 만약 없다면 from app.api.docs import CONFLICT 만 남기셔도 됩니다.
from app.api.docs import CONFLICT, NOT_FOUND 

router = APIRouter(prefix="/seats", tags=["Seats"])


@router.post(
    "", 
    response_model=ApiResponse[schemas.SeatResponse], 
    status_code=status.HTTP_201_CREATED,
    responses={**CONFLICT}
)
def create_seat(
    seat: schemas.SeatCreate,
    db: Session = Depends(get_db)
):
    """
    좌석 생성
    
    - **성공 시**: 201 Created와 함께 생성된 좌석 정보 반환
    - **실패 시**: 409 Conflict (이미 존재하는 좌석 ID)
    """
    # 1. 서비스 호출 (이미 존재하는 경우 서비스에서 ConflictException 발생)
    new_seat = seat_service.create_seat(db=db, seat_id=seat.seat_id)
    
    # 2. ORM -> Pydantic 변환
    seat_response = schemas.SeatResponse.model_validate(new_seat)

    # 3. 응답 반환
    return ApiResponse[schemas.SeatResponse](
        is_success=True,
        code=None,
        payload=seat_response
    )


@router.get(
    "", 
    response_model=ApiResponse[List[schemas.SeatResponse]]
)
def read_seats(db: Session = Depends(get_db)):
    """
    전체 좌석 조회
    """
    seats = seat_service.get_all_seats(db)
    
    # 리스트 내의 각 ORM 객체를 Pydantic 모델로 변환
    seat_responses = [schemas.SeatResponse.model_validate(s) for s in seats]

    return ApiResponse[List[schemas.SeatResponse]](
        is_success=True,
        code=None,
        payload=seat_responses
    )


@router.get(
    "/{seat_id}", 
    response_model=ApiResponse[schemas.SeatResponse],
    responses={**NOT_FOUND}
)
def read_seat(
    seat_id: int,
    db: Session = Depends(get_db)
):
    """
    특정 좌석 조회
    
    - **실패 시**: 404 Not Found (해당 ID의 좌석 없음)
    """
    seat = seat_service.get_seat(db, seat_id=seat_id)
    
    if seat is None:
        # 수동으로 ApiResponse를 리턴하는 대신, 예외를 발생시켜 핸들러가 처리하게 함
        raise BusinessException(
            code=ErrorCode.NOT_FOUND,
            message=f"좌석 ID {seat_id}번을 찾을 수 없습니다."
        )
    
    seat_response = schemas.SeatResponse.model_validate(seat)
    
    return ApiResponse[schemas.SeatResponse](
        is_success=True,
        code=None,
        payload=seat_response
    )