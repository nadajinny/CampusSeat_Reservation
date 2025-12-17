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

# 차단된 학번 목록
INVALID_STUDENT_IDS = {"202099999", "202288888"}


def login_student(db: Session, student_id: Union[int, str]) -> models.User:
    """
    학생 로그인 처리
    """
    normalized = _normalize_student_id(student_id)

    if normalized in INVALID_STUDENT_IDS:
        raise BusinessException(
            code=ErrorCode.AUTH_INVALID_STUDENT_ID,
            message="접근이 제한된 학번입니다.",
        )

    return get_or_create_user(db, int(normalized))


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


def _normalize_student_id(raw_id: Union[int, str]) -> str:
    """
    학번 문자열을 정규화하고 형식 오류를 BusinessException으로 변환.
    """
    if isinstance(raw_id, int):
        normalized = str(raw_id)
    elif isinstance(raw_id, str):
        normalized = raw_id.strip()
    else:
        raise BusinessException(
            code=ErrorCode.VALIDATION_ERROR,
            message="학번은 문자열 또는 숫자여야 합니다.",
        )

    if not (normalized.isdigit() and len(normalized) == 9):
        raise BusinessException(
            code=ErrorCode.VALIDATION_ERROR,
            message="학번은 정확히 9자리 숫자여야 합니다.",
        )

    return normalized
