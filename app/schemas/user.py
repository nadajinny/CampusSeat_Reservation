"""
schemas/user.py - User (Authentication) Schemas
===============================================
사용자 인증 관련 스키마 정의
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from pydantic import BaseModel, Field, field_serializer, field_validator


# -------------------------------------------------------------------
# 1. Base Schema (공통 속성)
# -------------------------------------------------------------------
class UserBase(BaseModel):
    """
    사용자 기본 정보.
    모든 인증 관련 스키마는 이 모델을 상속합니다.
    """

    student_id: int = Field(..., description="학번")

    # 학번 길이/형식 중앙 검증
    @field_validator("student_id", mode="before")
    @classmethod
    def validate_and_normalize_id(cls, value):
        if isinstance(value, int):
            normalized = str(value)
        elif isinstance(value, str):
            normalized = value.strip()
        else:
            raise ValueError("학번은 문자열 또는 숫자여야 합니다.")

        if not (len(normalized) == 9 and normalized.isdigit()):
            raise ValueError("학번은 정확히 9자리 숫자여야 합니다.")

        return int(normalized)


# -------------------------------------------------------------------
# 2. Request Schemas (요청)
# -------------------------------------------------------------------
class LoginRequest(UserBase):
    """로그인 요청은 학번만 필요합니다."""

    pass


# -------------------------------------------------------------------
# 3. Response Schemas (응답)
# -------------------------------------------------------------------
class TokenPayload(UserBase):
    """토큰 발급 응답"""

    access_token: str = Field(..., description="JWT 액세스 토큰")


KST = timezone(timedelta(hours=9))


class UserResponse(UserBase):
    last_login_at: Optional[datetime] = Field(None, description="마지막 로그인 일시")

    model_config = {"from_attributes": True}

    @field_serializer("last_login_at")
    def serialize_dt(self, dt: datetime, _info):
        if dt is None:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(KST).strftime("%Y-%m-%d %H:%M:%S")


# LoginResponse 타입을 명확히 정의 (기존 호환 유지 목적)
class LoginSuccessResponse(BaseModel):
    is_success: bool = True
    payload: TokenPayload


class LoginErrorResponse(BaseModel):
    is_success: bool = False
    code: str
    payload: dict
