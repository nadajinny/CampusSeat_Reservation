"""
app/scheduler.py
================
백그라운드 스케줄러 설정
매 분마다 예약 상태를 자동으로 변경합니다.
"""
from datetime import datetime, timezone
from sqlalchemy import update
from sqlalchemy.orm import Session
from apscheduler.schedulers.background import BackgroundScheduler

from app.database import SessionLocal
from app.models import Reservation, ReservationStatus

def update_reservation_status():
    """
    예약 상태 자동 동기화 작업 (Bulk Update)
    1. 시작 시간 도래 -> IN_USE (자동 시작)
    2. 종료 시간 도래 -> COMPLETED (자동 종료)
    """
    db: Session = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        
        # 1. [자동 시작] 예약 시간이 된 건들 -> '사용 중'으로 일괄 변경
        # "착한 사용자" 가정: 예약했으면 무조건 왔다고 침
        db.execute(
            update(Reservation)
            .where(
                Reservation.status == ReservationStatus.RESERVED,
                Reservation.start_time <= now
            )
            .values(status=ReservationStatus.IN_USE)
        )

        # 2. [자동 종료] 끝날 시간이 된 건들 -> '완료'로 일괄 변경
        # "사용 중"인 것만 완료 처리 (취소된 건 건드리지 않음)
        db.execute(
            update(Reservation)
            .where(
                Reservation.status == ReservationStatus.IN_USE,
                Reservation.end_time <= now
            )
            .values(status=ReservationStatus.COMPLETED)
        )
            
        db.commit()
        
    except Exception as e:
        print(f"[Scheduler Error] {e}")
        db.rollback()
    finally:
        db.close()

# 백그라운드 스케줄러 인스턴스 생성
scheduler = BackgroundScheduler()