"""
meeting_rooms.py - Meeting Room Reservation Endpoints
=====================================================
회의실 예약 관련 API 엔드포인트를 처리합니다.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from datetime import datetime, time as dt_time

from ..database import get_db
from .. import schemas, crud, constants

router = APIRouter(
    prefix="/api/reservations/meeting-rooms",
    tags=["Meeting Room Reservations"]
)


@router.post("", response_model=schemas.ApiResponse, status_code=status.HTTP_201_CREATED)
def create_meeting_room_reservation(
    request: schemas.MeetingRoomReservationCreate,
    db: Session = Depends(get_db)
):
    """
    회의실 예약 생성

    검증 항목:
    - 운영 시간: 09:00-18:00
    - 예약 시간: 정확히 1시간
    - 참여자: 최소 3명
    - 회의실 중복 방지
    - 다른 시설과 시간 겹침 방지
    - 일일 제한: 2시간
    - 주간 제한: 5시간
    """

    # TODO: 인증 미들웨어에서 student_id 가져오기
    # 현재는 임시로 하드코딩
    student_id = 202312345

    # 검증 1: 운영 시간 확인 (09:00-18:00)
    operation_start = dt_time(
        constants.OperationHours.START_HOUR,
        constants.OperationHours.START_MINUTE
    )
    operation_end = dt_time(
        constants.OperationHours.END_HOUR,
        constants.OperationHours.END_MINUTE
    )

    # time 객체를 timezone 제거 후 비교
    start_time_obj = request.start_time.replace(tzinfo=None) if hasattr(request.start_time, 'tzinfo') else request.start_time
    end_time_obj = request.end_time.replace(tzinfo=None) if hasattr(request.end_time, 'tzinfo') else request.end_time

    if start_time_obj < operation_start or end_time_obj > operation_end:
        return schemas.ApiResponse(
            is_success=False,
            code=constants.ErrorCode.TIME_OUT_OF_OPERATION_HOURS,
            payload={"message": "운영 시간(09:00-18:00)을 벗어났습니다."}
        )

    # 검증 2: 1시간 단위 확인
    start_dt = datetime.combine(request.date, request.start_time)
    end_dt = datetime.combine(request.date, request.end_time)
    duration_minutes = (end_dt - start_dt).total_seconds() / 60

    if duration_minutes != constants.ReservationLimits.MEETING_ROOM_SLOT_MINUTES:
        return schemas.ApiResponse(
            is_success=False,
            code=constants.ErrorCode.VALIDATION_ERROR,
            payload={"message": "회의실은 1시간 단위로만 예약 가능합니다."}
        )

    # 검증 3: 최소 참여자 수 확인
    if len(request.participants) < constants.ReservationLimits.MEETING_ROOM_MIN_PARTICIPANTS:
        return schemas.ApiResponse(
            is_success=False,
            code=constants.ErrorCode.PARTICIPANT_MIN_NOT_MET,
            payload={"message": "회의실 예약은 최소 3명의 참여자가 필요합니다."}
        )

    # 검증 4: 회의실 예약 가능 여부 확인
    if crud.check_room_conflict(db, request.room_id, start_dt):
        return schemas.ApiResponse(
            is_success=False,
            code=constants.ErrorCode.RESERVATION_CONFLICT,
            payload={"message": "해당 회의실이 이미 예약되어 있습니다."}
        )

    # 검증 5: 다른 시설과 시간 겹침 확인
    if crud.check_overlap_with_other_facility(db, student_id, start_dt):
        return schemas.ApiResponse(
            is_success=False,
            code=constants.ErrorCode.OVERLAP_WITH_OTHER_FACILITY,
            payload={"message": "동일 시간에 다른 시설 예약이 존재합니다."}
        )

    # 검증 6: 일일 제한 확인 (2시간 = 120분)
    daily_used = crud.check_user_daily_meeting_limit(db, student_id, start_dt)
    if daily_used + duration_minutes > constants.ReservationLimits.MEETING_ROOM_DAILY_LIMIT_MINUTES:
        return schemas.ApiResponse(
            is_success=False,
            code=constants.ErrorCode.DAILY_LIMIT_EXCEEDED,
            payload={
                "message": f"회의실 일일 이용 시간을 초과했습니다. 사용: {daily_used}분, 제한: 120분"
            }
        )

    # 검증 7: 주간 제한 확인 (5시간 = 300분)
    weekly_used = crud.check_user_weekly_meeting_limit(db, student_id, start_dt)
    if weekly_used + duration_minutes > constants.ReservationLimits.MEETING_ROOM_WEEKLY_LIMIT_MINUTES:
        return schemas.ApiResponse(
            is_success=False,
            code=constants.ErrorCode.WEEKLY_LIMIT_EXCEEDED,
            payload={
                "message": f"회의실 주간 이용 시간을 초과했습니다. 사용: {weekly_used}분, 제한: 300분"
            }
        )

    # 모든 검증 통과 - 예약 생성
    participants_data = [
        {"student_id": p.student_id, "name": p.name}
        for p in request.participants
    ]

    reservation = crud.create_meeting_room_reservation(
        db=db,
        student_id=student_id,
        room_id=request.room_id,
        start_time=start_dt,
        end_time=end_dt,
        participants=participants_data
    )

    # 응답 반환
    response_data = schemas.MeetingRoomReservationResponse(
        reservation_id=reservation.reservation_id,
        meeting_room_id=reservation.meeting_room_id,
        date=request.date,
        start_time=request.start_time,
        end_time=request.end_time,
        status=reservation.status.value  # Enum → string
    )

    return schemas.ApiResponse(
        is_success=True,
        code=None,
        payload=response_data.model_dump()
    )
