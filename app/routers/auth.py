"""
routers/auth.py - Authentication Endpoints
==========================================
Provides the `/api/auth/login` endpoint used in the assignment spec.
"""

from uuid import uuid4

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db

router = APIRouter(prefix="/api/auth", tags=["Auth"])

INVALID_STUDENT_IDS = {"202099999", "202288888"}


def _error_response(code: str, message: str, *, status_code: int) -> JSONResponse:
    """Builds a consistent error response body."""

    payload = schemas.LoginErrorResponse(
        code=code,
        payload=schemas.ErrorPayload(message=message),
    )
    return JSONResponse(
        status_code=status_code,
        content=payload.model_dump(),
    )


@router.post(
    "/login",
    response_model=schemas.LoginSuccessResponse,
    responses={
        400: {"model": schemas.LoginErrorResponse},
        401: {"model": schemas.LoginErrorResponse},
    },
)
def login(
    request: schemas.LoginRequest,
    db: Session = Depends(get_db),
):
    """
    Authenticate a student based on the assignment rules.

    - Accept 9-digit IDs only (validated here for custom error code)
    - Reject specific IDs with AUTH_INVALID_STUDENT_ID
    - Return an opaque access token together with the student_id
    - Upsert the user into the database for later reservation queries
    """

    normalized_id = request.student_id.strip()
    if not _is_valid_student_id(normalized_id):
        return _error_response(
            code="VALIDATION_ERROR",
            message="학번은 9자리 숫자여야 합니다.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    if normalized_id in INVALID_STUDENT_IDS:
        return _error_response(
            code="AUTH_INVALID_STUDENT_ID",
            message="유효하지 않은 학번입니다.",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    student_id_int = int(normalized_id)
    crud.upsert_user(db, student_id=student_id_int)

    token = f"token-{uuid4().hex}"
    payload = schemas.LoginSuccessResponse(
        payload=schemas.TokenPayload(
            access_token=token,
            student_id=student_id_int,
        )
    )
    return payload


def _is_valid_student_id(student_id: str) -> bool:
    """
    Check if the provided ID is a 9-digit numeric string.
    """

    return len(student_id) == 9 and student_id.isdigit()
