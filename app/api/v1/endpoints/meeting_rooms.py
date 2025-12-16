"""
api/v1/endpoints/meeting_rooms.py - Meeting Room Endpoints
==========================================================
회의실 예약 관련 API 엔드포인트

이 라우터는 Thin Controller 패턴을 따릅니다:
- HTTP 요청/응답 처리만 담당
- 모든 비즈니스 로직은 Service 계층에 위임
- 예외를 적절한 HTTP 응답으로 변환
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app import schemas
from app.schemas.common import ApiResponse
from app.services import meeting_room_service
from app.api.docs import CONFLICT, BAD_REQUEST

router = APIRouter(prefix="/reservations/meeting-rooms", tags=["Meeting Room Reservations"])


@router.post(
    "", 
    response_model=ApiResponse[schemas.ReservationResponse], 
    status_code=status.HTTP_201_CREATED,
    # [핵심] 여기에 에러 응답 문서화 추가!
    # 400, 409 에러가 발생할 수 있음을 Swagger에게 알려줌
    responses={
        **CONFLICT,     # 409 Conflict 예시
        **BAD_REQUEST   # 400 Bad Request 예시
    }
)
def create_meeting_room_reservation(
    request: schemas.MeetingRoomReservationCreate,
    db: Session = Depends(get_db)
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
    # TODO: 실제 인증 미들웨어가 붙으면 request.user.id 등으로 변경
    student_id = 202312345 

    # [수정 1] try-except 블록 제거!
    # 이제 에러가 발생하면 알아서 전역 핸들러(exception_handlers.py)로 날아갑니다.
    
    # 1. 서비스 호출 (결과는 SQLAlchemy ORM 객체)
    reservation_orm = meeting_room_service.process_reservation(
        db=db,
        request=request,
        student_id=student_id
    )

    # [수정 2] ORM 객체 -> Pydantic 스키마로 변환
    # SQLAlchemy 객체는 .model_dump()가 없으므로, Pydantic 모델의 model_validate를 사용합니다.
    reservation_schema = schemas.ReservationResponse.model_validate(reservation_orm)

    # 3. 공통 응답 포맷으로 래핑하여 반환
    return ApiResponse[schemas.ReservationResponse](
        is_success=True,
        code=None,
        payload=reservation_schema
    )
