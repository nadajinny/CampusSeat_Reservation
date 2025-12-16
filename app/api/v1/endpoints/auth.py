"""
api/v1/endpoints/auth.py - Authentication Endpoints
===================================================
인증 관련 API 엔드포인트
"""
from uuid import uuid4
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import user as user_schemas
from app.schemas.common import ApiResponse
from app.services import user_service
from app.exceptions import BusinessException

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post(
    "/login",
    response_model=ApiResponse[user_schemas.TokenPayload],
    status_code=status.HTTP_200_OK
)
def login(
    request: user_schemas.LoginRequest, # <-- 여기서 이미 9자리 숫자 검증 완료됨
    db: Session = Depends(get_db),
):
    """
    학생 로그인
    """
    try:
        # 1. 서비스 호출 (블랙리스트 확인 및 유저 생성)
        user = user_service.login_student(db, request.student_id)

        # 2. 토큰 생성
        token = f"token-{uuid4().hex}"

        # 3. 응답 반환
        return ApiResponse(
            is_success=True,
            code=None,
            payload=user_schemas.TokenPayload(
                student_id=user.student_id,
                access_token=token
            )
        )

    except BusinessException as e:
        # 비즈니스 로직 예외 처리 (예: 차단된 학번)
        return ApiResponse(
            is_success=False,
            code=e.code,
            payload={"message": e.message}
        )