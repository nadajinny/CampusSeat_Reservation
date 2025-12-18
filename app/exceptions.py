"""
exceptions.py - Custom Business Exceptions
==========================================
서비스 계층에서 발생하는 비즈니스 예외 정의
"""
from typing import Optional, Dict, Any
from app.constants import ErrorCode, ERROR_MESSAGES

class BusinessException(Exception):
    def __init__(
        self,
        code: ErrorCode, 
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None  # [New] 상세 정보 수신
    ):
        self.code = code
        # 메시지 자동 주입 로직
        self.message = message or ERROR_MESSAGES.get(code, "알 수 없는 오류")
        self.details = details
        super().__init__(self.message)


class ConflictException(BusinessException):
    pass

class ValidationException(BusinessException):
    pass

class LimitExceededException(BusinessException):
    pass

class ForbiddenException(BusinessException):
    pass