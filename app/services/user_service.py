"""
services/user_service.py - User Service
=======================================
사용자 관리 및 인증 관련 비즈니스 로직
"""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session

from .. import models
from ..exceptions import BusinessException
from ..constants import ErrorCode

# 차단된 학번 목록
INVALID_STUDENT_IDS = {"202099999", "202288888"}

def login_student(db: Session, student_id: int) -> models.User:
    """
    학생 로그인 처리
    """
    # 1. 블랙리스트 확인
    # 입력받은 student_id가 int형이므로 문자열 변환 후 비교하거나, set을 int로 관리
    if str(student_id) in INVALID_STUDENT_IDS:
        raise BusinessException(
            code=ErrorCode.AUTH_FORBIDDEN,
            message="접근이 제한된 학번입니다."
        )

    # 2. 유저 확보 (없으면 생성, 있으면 로그인 시간 갱신)
    return get_or_create_user(db, student_id)


def get_user(db: Session, student_id: int) -> Optional[models.User]:
    """학번으로 사용자 조회"""
    return db.query(models.User).filter(models.User.student_id == student_id).first()


def get_or_create_user(db: Session, student_id: int) -> models.User:
    """
    사용자가 있으면 반환(로그인 시간 업데이트), 없으면 생성 후 반환.
    """
    user = get_user(db, student_id)
    now_utc = datetime.now(timezone.utc)
    
    if user:
        # 기존 유저: 로그인 시간만 갱신
        user.last_login_at = now_utc
    else:
        # 신규 유저: 생성
        user = models.User(
            student_id=student_id,
            last_login_at=now_utc
        )
        db.add(user)
    
    db.commit()
    db.refresh(user)
    
    return user