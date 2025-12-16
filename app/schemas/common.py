"""
schemas/common.py - Common Schema Definitions
=============================================
공통으로 사용되는 스키마 정의 (Generic 적용)
"""

from typing import Optional, Generic, TypeVar, Union, Dict, Any
from pydantic import BaseModel, Field
from app.constants import ErrorCode

# 제네릭 타입 변수 선언
T = TypeVar("T")


class ErrorPayload(BaseModel):
    message: str = Field(..., description="에러 메시지")
    # [추가] 상세 에러 정보를 담을 수 있는 유연한 필드
    details: Optional[Dict[str, Any]] = Field(default=None, description="에러 상세 정보 (선택)")


class ApiResponse(BaseModel, Generic[T]):
    """
    공통 API 응답 포맷 (Generic)

    사용 예:
        ApiResponse[UserResponse](...)
        ApiResponse[List[SeatResponse]](...)
    """
    is_success: bool = Field(..., description="요청 성공 여부")
    code: Optional[ErrorCode] = Field(default=None, description="에러 코드 (실패 시)")
    payload: Optional[Union[T, ErrorPayload]] = Field(default=None, description="응답 데이터 (성공 시) 또는 에러 상세 (실패 시)")


class ErrorResponse(ApiResponse[ErrorPayload]):
    """Swagger에 4xx/5xx 에러 예시를 보여주기 위한 모델"""
    is_success: bool = Field(False, description="실패 시 항상 False")
    code: ErrorCode = Field(default=..., description="에러 코드", examples=["RESOURCE_CONFLICT"])