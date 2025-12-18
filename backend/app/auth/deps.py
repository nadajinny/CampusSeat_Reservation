"""
auth/deps.py - Authentication dependencies
==========================================
Authorization 헤더나 쿠키에서 학번을 추출하는 FastAPI 의존성.
토큰 형식: token-<student_id>-<random>
"""

from fastapi import Depends, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.constants import ErrorCode
from app.database import get_db
from app.exceptions import BusinessException
from app.services import user_service

# Bearer 헤더가 없을 때도 쿠키로 대체하기 위해 auto_error=False
bearer_scheme = HTTPBearer(auto_error=False)


def _extract_token(credentials: HTTPAuthorizationCredentials | None, request: Request) -> str:
    # 1) Authorization 헤더 우선
    if credentials and credentials.scheme.lower() == "bearer":
        return credentials.credentials.strip()

    # 2) access_token 쿠키
    cookie_token = request.cookies.get("access_token")
    if cookie_token:
        return cookie_token.strip()

    raise BusinessException(
        code=ErrorCode.AUTH_UNAUTHORIZED,
        message="인증 토큰이 없습니다.",
    )


def get_current_student_id(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
    request: Request = None,
    db: Session = Depends(get_db),
) -> int:
    """
    Bearer 헤더 또는 access_token 쿠키에서 token-<student_id>-<random>을 읽어 학번을 추출한다.
    """
    token = _extract_token(credentials, request)
    if not token.startswith("token-"):
        raise BusinessException(
            code=ErrorCode.AUTH_UNAUTHORIZED,
            message="토큰 형식이 올바르지 않습니다.",
        )

    parts = token.split("-", 2)  # token, student_id, random
    if len(parts) < 2:
        raise BusinessException(
            code=ErrorCode.AUTH_UNAUTHORIZED,
            message="토큰에서 학번을 찾을 수 없습니다.",
        )

    try:
        student_id = int(parts[1])
    except ValueError:
        raise BusinessException(
            code=ErrorCode.AUTH_UNAUTHORIZED,
            message="학번이 올바르지 않습니다.",
        )

    # 금지 학번 검증 및 존재 보장
    user_service.login_student(db, student_id)
    return student_id
