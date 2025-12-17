"""
api/v1/endpoints/auth.py - Authentication Endpoints
===================================================
인증 관련 API 엔드포인트

Thin Controller 패턴으로 로그인 API를 제공합니다.
- HTTP 요청/응답 래핑
- 비즈니스 로직은 service 계층으로 위임
- 예외는 일관된 ApiResponse로 변환
"""
from uuid import uuid4

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.responses import AUTH_ERROR_RESPONSE, VALIDATION_ERROR_RESPONSE
from app.constants import ErrorCode
from app.database import get_db
from app.exceptions import BusinessException
from app.schemas import user as user_schemas
from app.schemas.common import ApiResponse
from app.services import user_service

router = APIRouter(prefix="/auth", tags=["Auth"])

_ERROR_STATUS_MAP = {
    ErrorCode.VALIDATION_ERROR: status.HTTP_400_BAD_REQUEST,
    ErrorCode.AUTH_INVALID_STUDENT_ID: status.HTTP_401_UNAUTHORIZED,
    ErrorCode.AUTH_FORBIDDEN: status.HTTP_403_FORBIDDEN,
}


@router.post(
    "/login",
    response_model=ApiResponse[user_schemas.TokenPayload],
    status_code=status.HTTP_200_OK,
    responses=VALIDATION_ERROR_RESPONSE | AUTH_ERROR_RESPONSE,
)
def login(
    request: user_schemas.LoginRequest,
    db: Session = Depends(get_db),
):
    """
    학생 로그인 요청을 검증하고 토큰을 발급합니다.

    검증/비즈니스 규칙은 service 계층에서 처리됩니다.
    """
    try:
        user = user_service.login_student(db, request.student_id)
        token = f"token-{uuid4().hex}"
        return ApiResponse(
            is_success=True,
            code=None,
            payload=user_schemas.TokenPayload(
                student_id=user.student_id,
                access_token=token,
            ),
        )
    except BusinessException as exc:
        status_code = _ERROR_STATUS_MAP.get(exc.code, status.HTTP_400_BAD_REQUEST)
        error_body = ApiResponse(
            is_success=False,
            code=exc.code,
            payload={"message": exc.message},
        ).model_dump(mode="json")
        return JSONResponse(status_code=status_code, content=error_body)
