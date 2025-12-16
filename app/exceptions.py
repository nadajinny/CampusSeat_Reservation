"""
exceptions.py - Custom Business Exceptions
==========================================
서비스 계층에서 발생하는 비즈니스 예외 정의
"""

from dataclasses import dataclass


@dataclass
class BusinessException(Exception):
    """비즈니스 로직 예외 기본 클래스"""
    code: str
    message: str


@dataclass
class ValidationException(BusinessException):
    """검증 실패 예외"""
    pass


@dataclass
class ConflictException(BusinessException):
    """리소스 충돌 예외"""
    pass


@dataclass
class LimitExceededException(BusinessException):
    """제한 초과 예외"""
    pass
