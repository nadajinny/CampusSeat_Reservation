from app.schemas.common import ErrorResponse
from app.constants import ErrorCode, ERROR_MESSAGES

BAD_REQUEST = {
    400: {
        "model": ErrorResponse,
        "description": "잘못된 요청",
        "content": {
            "application/json": {
                "example": {
                    "is_success": False,
                    "code": ErrorCode.VALIDATION_ERROR,
                    "payload": {
                        "message": ERROR_MESSAGES[ErrorCode.VALIDATION_ERROR],
                        "details": {"reason": "example detail"}
                    }
                }
            }
        }
    }
}

NOT_FOUND = {
    404: {
        "model": ErrorResponse,
        "description": "리소스를 찾을 수 없음",
        "content": {
            "application/json": {
                "example": {
                    "is_success": False,
                    "code": ErrorCode.NOT_FOUND,
                    "payload": {"message": ERROR_MESSAGES[ErrorCode.NOT_FOUND]}
                }
            }
        }
    }
}

CONFLICT = {
    409: {
        "model": ErrorResponse,
        "description": "리소스 충돌",
        "content": {
            "application/json": {
                "example": {
                    "is_success": False,
                    "code": ErrorCode.RESERVATION_CONFLICT,
                    "payload": {"message": ERROR_MESSAGES[ErrorCode.RESERVATION_CONFLICT]}
                }
            }
        }
    }
}