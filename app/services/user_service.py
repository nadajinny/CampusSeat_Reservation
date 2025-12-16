"""
services/user_service.py - User Service
=======================================
사용자 관리 및 인증 관련 비즈니스 로직
"""

from datetime import datetime, timezone
from sqlalchemy.orm import Session

from .. import models, constants
from ..exceptions import BusinessException

# 차단된 학번 목록 (비즈니스 규칙)
INVALID_STUDENT_IDS = {"202099999", "202288888"}

def login_student(db: Session, student_id_str: str) -> models.User:
    """
    학생 로그인 처리 (비즈니스 로직)
    """
    # 1. 블랙리스트 확인 (비즈니스 검증)
    if student_id_str in INVALID_STUDENT_IDS:
        raise BusinessException(
            code="AUTH_INVALID_STUDENT_ID", # constants에 정의된 코드로 변경 권장
            message="유효하지 않은 학번입니다."
        )

    # 2. 형 변환 및 User Upsert 호출
    student_id = int(student_id_str)
    return get_or_create_user(db, student_id)

def get_user(db: Session, student_id: int) -> models.User | None:
    """학번으로 사용자 조회"""
    return db.query(models.User).filter(models.User.student_id == student_id).first()


def get_or_create_user(db: Session, student_id: int) -> models.User:
    """
    사용자가 있으면 반환(로그인 시간 업데이트), 없으면 생성 후 반환.
    
    모든 예약 로직의 첫 단추로 사용됩니다.
    """
    user = get_user(db, student_id)
    
    now_utc = datetime.now(timezone.utc)
    
    if user:
        # 기존 유저: 로그인 시간만 갱신 (Dirty Checking)
        user.last_login_at = now_utc
    else:
        # 신규 유저: 생성
        user = models.User(
            student_id=student_id,
            last_login_at=now_utc
        )
        db.add(user)
    
    # 변경사항 반영
    db.commit()
    db.refresh(user)
    
    return user