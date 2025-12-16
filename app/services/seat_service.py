"""
services/seat_service.py - Seat Service
=======================================
좌석 관리 관련 비즈니스 로직
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from .. import models
from ..exceptions import ConflictException

def get_seat(db: Session, seat_id: int) -> Optional[models.Seat]:
    """좌석 단건 조회"""
    return db.query(models.Seat).filter(models.Seat.seat_id == seat_id).first()


def get_all_seats(db: Session) -> List[models.Seat]:
    """전체 좌석 목록 조회"""
    return db.query(models.Seat).order_by(models.Seat.seat_id).all()


def get_seats_count(db: Session) -> int:
    """전체 좌석 수 조회"""
    return db.query(models.Seat).count()


def create_seat(db: Session, seat_id: int) -> models.Seat:
    """
    좌석 생성 (중복 체크 포함)
    
    Args:
        db: 데이터베이스 세션
        seat_id: 생성할 좌석 ID (int)
        
    Raises:
        ConflictException: 이미 존재하는 좌석 ID일 경우
    """
    # 1. 중복 체크 (비즈니스 로직)
    if get_seat(db, seat_id):
        raise ConflictException(
            code="SEAT_ALREADY_EXISTS",
            message=f"좌석 ID {seat_id}번은 이미 존재합니다."
        )

    # 2. 생성 (Action)
    db_seat = models.Seat(
        seat_id=seat_id,
        is_available=True  # 기본값
    )
    db.add(db_seat)
    db.commit()
    db.refresh(db_seat)
    
    return db_seat