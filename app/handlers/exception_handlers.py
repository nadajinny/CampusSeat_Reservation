from typing import Type
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.exceptions import (
    BusinessException,
    ConflictException,
    ValidationException,
    LimitExceededException
)
from app.constants import ErrorCode, ERROR_MESSAGES
from app.schemas.common import ApiResponse, ErrorPayload

# --------------------------------------------------------------------------
# 1. 예외 타입별 HTTP 상태 코드 매핑 테이블
# --------------------------------------------------------------------------
EXCEPTION_STATUS_MAP: dict[Type[BusinessException], int] = {
    ConflictException: status.HTTP_409_CONFLICT,
    ValidationException: status.HTTP_400_BAD_REQUEST,
    LimitExceededException: status.HTTP_400_BAD_REQUEST,
}

# --------------------------------------------------------------------------
# 2. 비즈니스 예외 핸들러 (수정됨)
# --------------------------------------------------------------------------
# [핵심 변경] exc 타입을 Exception으로 넓혀서 add_exception_handler의 타입 규칙을 만족시킴
async def business_exception_handler(request: Request, exc: Exception):
    
    # [안전장치] 실제로 BusinessException(또는 그 자식)이 맞는지 런타임 체크
    # main.py에서 BusinessException으로 등록했으므로 거의 항상 True지만,
    # 타입 체커(Pylance)와 만약의 등록 실수를 위해 필요합니다.
    if not isinstance(exc, BusinessException):
        # 만약 BusinessException이 아닌 다른 에러가 이 핸들러로 들어왔다면 500 처리
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ApiResponse[ErrorPayload](
                is_success=False,
                code=ErrorCode.INTERNAL_SERVER_ERROR,
                payload=ErrorPayload(message="Internal Type Error")
            ).model_dump(mode='json')
        )

    # 이 아래부터는 exc가 BusinessException임이 보장됨
    http_status = EXCEPTION_STATUS_MAP.get(type(exc), status.HTTP_400_BAD_REQUEST)

    error_payload = ErrorPayload(
        message=exc.message,
        details=exc.details
    )

    return JSONResponse(
        status_code=http_status,
        content=ApiResponse[ErrorPayload](
            is_success=False,
            code=exc.code,
            payload=error_payload
        ).model_dump(mode='json')
    )

# --------------------------------------------------------------------------
# 3. 입력값 검증 예외 핸들러 (RequestValidationError - 422)
# --------------------------------------------------------------------------
async def validation_exception_handler(request: Request, exc: Exception):
    error_details = []
    
    # 1. 에러 상세 정보 정제 (ctx 제거)
    for error in exc.errors():
        new_error = error.copy()
        if "ctx" in new_error:
            del new_error["ctx"]
        if "url" in new_error:
            del new_error["url"]
        error_details.append(new_error)

    # 2. 사용자에게 보여줄 메시지 추출 및 정제
    if error_details:
        # Pydantic이 붙인 "Value error, " 접두어 제거
        raw_msg = error_details[0].get('msg', "Unknown error")
        clean_msg = raw_msg.replace("Value error, ", "") # [핵심 수정] 접두어 삭제
    else:
        clean_msg = "Unknown error"
        
    # 3. 최종 메시지 조합
    # "입력 값이 올바르지 않습니다." 같은 고정 문구 대신, 구체적인 에러 내용을 바로 보여줍니다.
    # 원하시면 f"입력 오류: {clean_msg}" 형태로 감싸도 됩니다.
    error_msg = clean_msg
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=ApiResponse[ErrorPayload](
            is_success=False,
            code=ErrorCode.VALIDATION_ERROR,
            payload=ErrorPayload(
                message=error_msg,  # 정제된 메시지 ("종료 시간은 시작 시간보다...")
                details={"pydantic_errors": error_details}
            )
        ).model_dump(mode='json')
    )

# --------------------------------------------------------------------------
# 4. 서버 내부 예외 핸들러 (Exception - 500)
# --------------------------------------------------------------------------
async def internal_exception_handler(request: Request, exc: Exception):
    # 실무에서는 여기서 Sentry 등으로 로깅
    # import traceback; traceback.print_exc()
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ApiResponse[ErrorPayload](
            is_success=False,
            code=ErrorCode.INTERNAL_SERVER_ERROR,
            payload=ErrorPayload(
                message=ERROR_MESSAGES[ErrorCode.INTERNAL_SERVER_ERROR]
            )
        ).model_dump(mode='json')
    )