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
from sqlalchemy.orm import Session

from app.api.docs import BAD_REQUEST, FORBIDDEN, UNAUTHORIZED
from app.database import get_db
from app.schemas import user as user_schemas
from app.schemas.common import ApiResponse
from app.services import user_service

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/login",
    response_model=ApiResponse[user_schemas.TokenPayload],
    status_code=status.HTTP_200_OK,
    responses={**BAD_REQUEST, **UNAUTHORIZED, **FORBIDDEN},
)
def login(
    request: user_schemas.LoginRequest,
    db: Session = Depends(get_db),
):
    """
    학생 로그인 요청을 검증하고 토큰을 발급합니다.

    검증/비즈니스 규칙은 service 계층에서 처리됩니다.
    """
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
