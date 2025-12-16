"""
schemas/user.py - User (Authentication) Schemas
===============================================
사용자 인증 관련 스키마 정의
"""

from typing import Optional
from pydantic import BaseModel, Field, field_validator, field_serializer
from datetime import datetime, timezone, timedelta

# -------------------------------------------------------------------
# 1. Base Schema (공통 속성)
# -------------------------------------------------------------------
class UserBase(BaseModel):
    """
    사용자 기본 정보
    - 모든 곳에서 '유저'를 참조할 때 이 스키마를 상속하거나 사용합니다.
    """
    student_id: int = Field(..., description="학번")

    # [핵심] 학번 길이 검증 로직을 여기로 이동 (중앙 관리)
    @field_validator("student_id", mode="before")
    @classmethod
    def validate_and_normalize_id(cls, v):
        # 1. 타입 유연성 처리 (int -> str) 및 공백 제거
        if isinstance(v, int):
            v = str(v)
        elif isinstance(v, str):
            v = v.strip()
        else:
            raise ValueError("학번은 문자열 또는 숫자여야 합니다.")

        # 2. [핵심] Pydantic 검증 로직 추가 (9자리 숫자)
        if not (len(v) == 9 and v.isdigit()):
            raise ValueError("학번은 정확히 9자리 숫자여야 합니다.")
        return v


# -------------------------------------------------------------------
# 2. Request Schemas (요청)
# -------------------------------------------------------------------
class LoginRequest(UserBase):
    """로그인 요청은 학번만 있으면 됨"""
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

    @field_serializer('last_login_at')
    def serialize_dt(self, dt: datetime, _info):
        if dt is None:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(KST).strftime("%Y-%m-%d %H:%M:%S")


# LoginResponse 타입을 명확히 정의 (성공/실패 분리 없이 ApiResponse로 통일 권장하지만, 기존 호환 유지)
class LoginSuccessResponse(BaseModel):
    is_success: bool = True
    payload: TokenPayload

class LoginErrorResponse(BaseModel):
    is_success: bool = False
    code: str
    payload: dict