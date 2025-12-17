"""
api/v1/endpoints/reservations.py - My Reservations endpoints.
"""

from datetime import date as Date, datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app import schemas
from app.constants import ReservationType
from app.database import get_db
from app.services import reservation_service

router = APIRouter(prefix="/reservations", tags=["My Reservations"])

KST = timezone(timedelta(hours=9))


@router.get(
    "/me",
    response_model=schemas.ApiResponse[schemas.MyReservationsPayload],
    summary="내 예약 목록 조회",
    description="""
    본인의 예약 내역을 조회합니다 (회의실 + 좌석 통합).

    Query Parameters (선택):
    - from: 시작 날짜 (YYYY-MM-DD)
    - to: 종료 날짜 (YYYY-MM-DD)
    - type: 예약 유형 필터 (meeting_room | seat)
    """,
)
def get_my_reservations(
    from_date: Optional[Date] = Query(None, alias="from", description="시작 날짜 (YYYY-MM-DD)"),
    to_date: Optional[Date] = Query(None, alias="to", description="종료 날짜 (YYYY-MM-DD)"),
    reservation_type: Optional[str] = Query(None, alias="type", description="예약 유형 (meeting_room | seat)"),
    db: Session = Depends(get_db),
):
    """
    내 예약 목록 조회

    """
    # TODO: 인증 연동 후 request.user.id에서 student_id 추출
    student_id = 202312345

    # 1. DB에서 모든 예약 조회
    reservations = reservation_service.get_user_reservations(db, student_id)

    # 2. 날짜 및 타입 필터링
    filtered_items = []
    for res in reservations:
        # UTC -> KST 변환
        start_kst = res.start_time.replace(tzinfo=timezone.utc).astimezone(KST) if res.start_time.tzinfo is None else res.start_time.astimezone(KST)
        end_kst = res.end_time.replace(tzinfo=timezone.utc).astimezone(KST) if res.end_time.tzinfo is None else res.end_time.astimezone(KST)

        # 날짜 필터링
        res_date = start_kst.date()
        if from_date and res_date < from_date:
            continue
        if to_date and res_date > to_date:
            continue

        # 타입 결정
        if res.meeting_room_id is not None:
            item_type = ReservationType.MEETING_ROOM
            room_id = res.meeting_room_id
            seat_id = None
        else:
            item_type = ReservationType.SEAT
            room_id = None
            seat_id = res.seat_id

        # 타입 필터링
        if reservation_type and item_type != reservation_type:
            continue

        # 상태 변환
        status_value = res.status.value if hasattr(res.status, "value") else res.status

        # 아이템 생성
        item = schemas.MyReservationItem(
            reservation_id=res.reservation_id,
            type=item_type,
            room_id=room_id,
            seat_id=seat_id,
            date=res_date.isoformat(),
            start_time=start_kst.strftime("%H:%M"),
            end_time=end_kst.strftime("%H:%M"),
            status=status_value,
        )
        filtered_items.append(item)

    # 3. 응답 생성
    payload = schemas.MyReservationsPayload(items=filtered_items)

    return schemas.ApiResponse[schemas.MyReservationsPayload](
        is_success=True,
        code=None,
        payload=payload,
    )
