"""
api/responses.py - Reusable OpenAPI error response templates.
"""

from __future__ import annotations

from ..schemas.common import ErrorResponseModel

VALIDATION_ERROR_RESPONSE = {
    400: {
        "model": ErrorResponseModel,
        "description": "잘못된 요청 (형식 오류, 입력 누락 등)",
    }
}

AUTH_ERROR_RESPONSE = {
    401: {
        "model": ErrorResponseModel,
        "description": "인증 실패 (차단 학번 또는 토큰 오류)",
    }
}

CONFLICT_ERROR_RESPONSE = {
    409: {
        "model": ErrorResponseModel,
        "description": "리소스 충돌 (이미 존재하는 예약 등)",
    }
}
