"""
schemas/common.py - Common Schema Definitions
=============================================
공통으로 사용되는 스키마 정의 (Generic 적용)
"""

from typing import Optional, Generic, TypeVar
from pydantic import BaseModel, Field

# 제네릭 타입 변수 선언
T = TypeVar("T")


class ErrorPayload(BaseModel):
    """에러 발생 시 상세 메시지"""
    message: str


class ApiResponse(BaseModel, Generic[T]):
    """
    공통 API 응답 포맷 (Generic)

    사용 예:
        ApiResponse[UserResponse](...)
        ApiResponse[List[SeatResponse]](...)
    """
    is_success: bool = Field(..., description="요청 성공 여부")
    code: Optional[str] = Field(None, description="에러 코드 (실패 시)")
    payload: Optional[T] = Field(None, description="응답 데이터 (성공 시) 또는 에러 상세 (실패 시)")
