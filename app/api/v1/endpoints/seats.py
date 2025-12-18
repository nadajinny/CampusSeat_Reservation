"""
api/v1/endpoints/seats.py - Seat metadata & reservation endpoints.
"""

from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app import schemas
from app.api.docs import BAD_REQUEST, CONFLICT, NOT_FOUND
from app.constants import ErrorCode, ReservationType
from app.database import get_db
from app.exceptions import BusinessException
from app.schemas.common import ApiResponse
from app.services import seat_service

# Seat metadata router (/seats)
router = APIRouter(prefix="/seats", tags=["Seats"])

# Seat reservation router (/reservations/seats)
reservation_router = APIRouter(
    prefix="/reservations/seats",
    tags=["Seat Reservations"],
)


@router.post(
    "",
    response_model=ApiResponse[schemas.SeatResponse],
    status_code=status.HTTP_201_CREATED,
    responses={**CONFLICT},
)
def create_seat(seat: schemas.SeatCreate, db: Session = Depends(get_db)):
    """
    좌석 생성
    """

    new_seat = seat_service.create_seat(db=db, seat_id=seat.seat_id)
    seat_response = schemas.SeatResponse.model_validate(new_seat)

    return ApiResponse[schemas.SeatResponse](
        is_success=True,
        code=None,
        payload=seat_response,
    )


@router.get(
    "",
    response_model=ApiResponse[List[schemas.SeatResponse]],
)
def read_seats(db: Session = Depends(get_db)):
    """
    전체 좌석 조회
    """

    seats = seat_service.get_all_seats(db)
    seat_responses = [schemas.SeatResponse.model_validate(item) for item in seats]

    return ApiResponse[List[schemas.SeatResponse]](
        is_success=True,
        code=None,
        payload=seat_responses,
    )


@router.get(
    "/{seat_id}",
    response_model=ApiResponse[schemas.SeatResponse],
    responses={**NOT_FOUND},
)
def read_seat(seat_id: int, db: Session = Depends(get_db)):
    """
    특정 좌석 조회
    """

    seat = seat_service.get_seat(db, seat_id=seat_id)
    if seat is None:
        raise BusinessException(
            code=ErrorCode.NOT_FOUND,
            message=f"좌석 ID {seat_id}번을 찾을 수 없습니다.",
        )

    seat_response = schemas.SeatResponse.model_validate(seat)
    return ApiResponse[schemas.SeatResponse](
        is_success=True,
        code=None,
        payload=seat_response,
    )


@reservation_router.post(
    "",
    response_model=ApiResponse[schemas.SeatReservationResponse],
    status_code=status.HTTP_201_CREATED,
    responses={**BAD_REQUEST, **CONFLICT},
)
def create_seat_reservation(
    request: schemas.SeatReservationCreate,
    db: Session = Depends(get_db),
):
    """
    좌석 예약 생성
    
    검증 항목 (Service 계층에서 처리):
    - 운영시간/2시간 단위
    - 해당 좌석 동일 시간대 중복 금지
    - 본인 좌석 1일 4시간 초과 금지
    - 동일 시간대 회의실 예약(본인) 존재 금지
    """

    # TODO: 인증 연동 후 request.user.id에서 student_id를 추출
    student_id = 202312345
    reservation = seat_service.reserve_seat(db, student_id, request)

    status_value = (
        reservation.status.value if hasattr(reservation.status, "value") else reservation.status
    )
    payload = schemas.SeatReservationResponse(
        reservation_id=reservation.reservation_id,
        seat_id=reservation.seat_id or request.seat_id,
        date=request.date.isoformat(),
        start_time=request.start_time.strftime("%H:%M"),
        end_time=request.end_time.strftime("%H:%M"),
        status=status_value,
        type=ReservationType.SEAT,
    )

    return ApiResponse[schemas.SeatReservationResponse](
        is_success=True,
        code=None,
        payload=payload,
    )


@reservation_router.post(
    "/random",
    response_model=ApiResponse[schemas.SeatReservationResponse],
    status_code=status.HTTP_201_CREATED,
    responses={**BAD_REQUEST, **CONFLICT},
    summary="랜덤 좌석 예약",
    description="""
    가용한 좌석 중 하나를 자동으로 배정하여 예약합니다.

    검증 항목 (Service 계층에서 처리):
    - 운영시간/2시간 단위
    - 가용 좌석 존재 여부
    - 본인 좌석 1일 4시간 초과 금지
    - 동일 시간대 회의실 예약(본인) 존재 금지

    에러:
    - 409 CONFLICT: 해당 시간대에 예약 가능한 좌석이 없습니다.
    """,
)
def create_random_seat_reservation(
    request: schemas.SeatReservationCreate,
    db: Session = Depends(get_db),
):
    """
    랜덤 좌석 예약 생성

    """
    # TODO: 인증 연동 후 request.user.id에서 student_id 추출
    student_id = 202312345

    # seat_id를 강제로 None으로 설정하여 랜덤 모드 활성화
    request.seat_id = None

    # 기존 reserve_seat 함수 재사용
    reservation = seat_service.reserve_seat(db, student_id, request)

    # 응답 생성
    status_value = (
        reservation.status.value if hasattr(reservation.status, "value") else reservation.status
    )
    payload = schemas.SeatReservationResponse(
        reservation_id=reservation.reservation_id,
        seat_id=reservation.seat_id,  # 랜덤 배정된 seat_id
        date=request.date.isoformat(),
        start_time=request.start_time.strftime("%H:%M"),
        end_time=request.end_time.strftime("%H:%M"),
        status=status_value,
        type=ReservationType.SEAT,
    )

    return ApiResponse[schemas.SeatReservationResponse](
        is_success=True,
        code=None,
        payload=payload,
    )
