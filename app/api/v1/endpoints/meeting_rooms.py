"""
api/v1/endpoints/meeting_rooms.py - Meeting Room Endpoints
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app import schemas
from app.api.docs import BAD_REQUEST, CONFLICT
from app.database import get_db
from app.auth.deps import get_current_student_id
from app.schemas.common import ApiResponse
from app.services import meeting_room_service

router = APIRouter(prefix="/reservations/meeting-rooms", tags=["Meeting Room Reservations"])


@router.post(
    "",
    response_model=ApiResponse[schemas.ReservationResponse],
    status_code=status.HTTP_201_CREATED,
    responses={**CONFLICT, **BAD_REQUEST},
)
def create_meeting_room_reservation(
    request: schemas.MeetingRoomReservationCreate,
    db: Session = Depends(get_db),
    student_id: int = Depends(get_current_student_id),
):
    """
    회의실 예약 생성

    검증 항목 (Service 계층에서 처리):
    - 운영 시간: 09:00-18:00
    - 예약 시간: 정확히 1시간
    - 참여자: 최소 3명
    - 회의실 중복 방지
    - 다른 시설과 시간 겹침 방지
    - 일일 제한: 2시간
    - 주간 제한: 5시간
    """
    reservation_orm = meeting_room_service.process_reservation(
        db=db,
        request=request,
        student_id=student_id
    )

    reservation_schema = schemas.ReservationResponse.model_validate(reservation_orm)

    return ApiResponse[schemas.ReservationResponse](
        is_success=True,
        code=None,
        payload=reservation_schema
    )
