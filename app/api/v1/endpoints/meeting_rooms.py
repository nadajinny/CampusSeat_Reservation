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

from ....database import get_db
from ....schemas import meeting_room as meeting_room_schemas
from ....schemas.common import ApiResponse
from ....services import meeting_room_service
from ....exceptions import BusinessException

router = APIRouter(prefix="/reservations/meeting-rooms", tags=["Meeting Room Reservations"])


@router.post("", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
def create_meeting_room_reservation(
    request: meeting_room_schemas.MeetingRoomReservationCreate,
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
    # TODO: 인증 미들웨어에서 student_id 가져오기
    student_id = 202312345

    try:
        # 모든 검증과 생성 로직을 Service에 위임
        response_data = meeting_room_service.process_reservation(
            db=db,
            request=request,
            student_id=student_id
        )

        return ApiResponse(
            is_success=True,
            code=None,
            payload=response_data.model_dump()
        )

    except BusinessException as e:
        # 비즈니스 예외를 API 응답으로 변환
        return ApiResponse(
            is_success=False,
            code=e.code,
            payload={"message": e.message}
        )
