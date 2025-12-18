"""
services/user_service.py - User Service
=======================================
사용자 관리 및 인증 관련 비즈니스 로직
"""

from datetime import datetime, timezone
from typing import Optional, Union

from sqlalchemy.orm import Session

from app import models
from app.constants import ErrorCode
from app.exceptions import BusinessException

# 차단된 학번 목록 (정수로 보관하여 입력 타입에 상관없이 일관 비교)
INVALID_STUDENT_IDS = {202099999, 202288888}


def login_student(db: Session, student_id: Union[int, str]) -> models.User:
    """
    학생 로그인 처리
    """

    normalized_id = int(student_id)

    if normalized_id in INVALID_STUDENT_IDS:
        raise BusinessException(
            code=ErrorCode.AUTH_INVALID_STUDENT_ID,
            message="접근이 제한된 학번입니다.",
        )

    return get_or_create_user(db, normalized_id)


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
            last_login_at=now_utc,
        )
        db.add(user)

    db.commit()
    db.refresh(user)

    return user
