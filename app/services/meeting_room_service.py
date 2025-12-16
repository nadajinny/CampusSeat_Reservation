"""
services/meeting_room_service.py - Meeting Room Service
=======================================================
회의실 예약 프로세스 조율 및 비즈니스 로직 (Facade)
"""

from datetime import datetime, timedelta, date, time, timezone
from typing import List
from sqlalchemy.orm import Session

from .. import models, schemas, constants
from . import user_service, reservation_service

# 한국 시간대 정의
KST = timezone(timedelta(hours=9))

def process_reservation(
    db: Session, 
    student_id: int, 
    request: schemas.MeetingRoomReservationCreate
) -> models.Reservation:
    
    # ---------------------------------------------------
    # 1. 데이터 가공 (KST 입력 -> UTC 변환)
    # ---------------------------------------------------
    # 1-1. 날짜 + 시간 합치기 (이때 KST 정보를 붙여야 함!)
    start_dt_kst = datetime.combine(request.date, request.start_time, tzinfo=KST)
    end_dt_kst = datetime.combine(request.date, request.end_time, tzinfo=KST)

    # 1-2. DB 저장을 위해 UTC로 변환
    start_dt_utc = start_dt_kst.astimezone(timezone.utc)
    end_dt_utc = end_dt_kst.astimezone(timezone.utc)

    # 1-3. 이용 시간 계산
    duration_minutes = (end_dt_utc - start_dt_utc).total_seconds() / 60

    # ---------------------------------------------------
    # 2. 비즈니스 로직 검증 (여기서는 UTC 시간을 사용)
    # ---------------------------------------------------
    # DB에는 UTC가 들어있고, 우리가 만든 start_dt_utc도 UTC이므로 비교 OK
    
    if check_room_conflict(db, request.room_id, start_dt_utc):
        raise ValueError("해당 회의실은 이미 예약되어 있습니다.")

    if reservation_service.check_overlap_with_other_facility(db, student_id, start_dt_utc):
        raise ValueError("동일 시간에 다른 시설 예약이 존재합니다.")

    # 2-3. 일일 이용 한도 확인
    daily_used = check_user_daily_meeting_limit(db, student_id, start_dt_utc)
    limit_daily = constants.ReservationLimits.MEETING_ROOM_DAILY_LIMIT_MINUTES
    if daily_used + duration_minutes > limit_daily:
        raise ValueError(f"일일 이용 한도({limit_daily}분)를 초과했습니다. (현재: {daily_used}분 사용 중)")

    # 2-4. 주간 이용 한도 확인
    weekly_used = check_user_weekly_meeting_limit(db, student_id, start_dt_utc)
    limit_weekly = constants.ReservationLimits.MEETING_ROOM_WEEKLY_LIMIT_MINUTES
    if weekly_used + duration_minutes > limit_weekly:
        raise ValueError(f"주간 이용 한도({limit_weekly}분)를 초과했습니다. (현재: {weekly_used}분 사용 중)")

    # ---------------------------------------------------
    # 3. 유저 처리 및 예약 생성 (Action)
    # ---------------------------------------------------
    
    # 3-1. 예약자(메인 유저) 확보
    user_service.get_or_create_user(db, student_id)

    # 3-2. 참여자들 확보 (참여자들도 User 테이블에 있어야 함)
    participant_ids = []
    for p in request.participants:
        user_service.get_or_create_user(db, p.student_id)
        participant_ids.append(p.student_id)

    # 3-3. 최종 예약 생성 (Reservation Service에게 위임)
    new_reservation = reservation_service.create_meeting_room_reservation(
        db=db,
        student_id=student_id,
        room_id=request.room_id,
        start_time=start_dt_utc,
        end_time=end_dt_utc,
        participant_ids=participant_ids
    )

    return new_reservation


# --- 내부 지원 함수들 (DB 조회용) ---

def check_room_conflict(db: Session, room_id: int, start_time: datetime) -> bool:
    """회의실 중복 예약 확인"""
    conflict = db.query(models.Reservation).filter(
        models.Reservation.meeting_room_id == room_id,
        models.Reservation.start_time == start_time,
        models.Reservation.status == models.ReservationStatus.RESERVED
    ).first()
    return conflict is not None


def check_user_daily_meeting_limit(db: Session, student_id: int, target_date: datetime) -> int:
    """일일 사용량 계산"""
    start_of_day = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)

    reservations = db.query(models.Reservation).filter(
        models.Reservation.student_id == student_id,
        models.Reservation.meeting_room_id.isnot(None),
        models.Reservation.status == models.ReservationStatus.RESERVED,
        models.Reservation.start_time >= start_of_day,
        models.Reservation.start_time <= end_of_day
    ).all()

    return _calculate_total_minutes(reservations)


def check_user_weekly_meeting_limit(db: Session, student_id: int, target_date: datetime) -> int:
    """주간 사용량 계산"""
    start_of_week = target_date - timedelta(days=target_date.weekday())
    start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_week = start_of_week + timedelta(days=6, hours=23, minutes=59, seconds=59)

    reservations = db.query(models.Reservation).filter(
        models.Reservation.student_id == student_id,
        models.Reservation.meeting_room_id.isnot(None),
        models.Reservation.status == models.ReservationStatus.RESERVED,
        models.Reservation.start_time >= start_of_week,
        models.Reservation.start_time <= end_of_week
    ).all()

    return _calculate_total_minutes(reservations)


def get_meeting_room_count(db: Session) -> int:
    return db.query(models.MeetingRoom).count()


def _calculate_total_minutes(reservations: List[models.Reservation]) -> int:
    """예약 리스트의 총 시간을 분 단위로 계산"""
    return int(sum(
        (r.end_time - r.start_time).total_seconds() / 60
        for r in reservations
    ))