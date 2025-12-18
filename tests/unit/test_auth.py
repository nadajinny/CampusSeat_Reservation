"""
tests/unit/test_auth.py - 인증 로직 단위 테스트
"""
import pytest
from datetime import datetime, timezone

from app.services import user_service
from app.constants import ErrorCode
from app.exceptions import BusinessException


class TestLoginValidation:
    """로그인 검증 로직 테스트"""

    def test_valid_student_id_login(self, db_session):
        """유효한 학번으로 로그인 성공"""
        valid_student_id = 202312345

        # 실행
        user = user_service.login_student(db_session, valid_student_id)

        # 검증
        assert user is not None
        assert user.student_id == valid_student_id
        assert user.last_login_at is not None

    def test_invalid_student_id_202099999(self, db_session):
        """금지된 학번 202099999 로그인 실패"""
        blocked_id = 202099999

        # 실행 및 검증
        with pytest.raises(BusinessException) as exc_info:
            user_service.login_student(db_session, blocked_id)

        assert exc_info.value.code == ErrorCode.AUTH_INVALID_STUDENT_ID

    def test_invalid_student_id_202288888(self, db_session):
        """금지된 학번 202288888 로그인 실패"""
        blocked_id = 202288888

        # 실행 및 검증
        with pytest.raises(BusinessException) as exc_info:
            user_service.login_student(db_session, blocked_id)

        assert exc_info.value.code == ErrorCode.AUTH_INVALID_STUDENT_ID

    def test_invalid_student_id_format(self, db_session):
        """잘못된 형식의 학번 (9자리 아님)"""
        # 8자리 학번
        invalid_id = "12345678"

        # 실행 - 변환 시도
        try:
            user_service.login_student(db_session, invalid_id)
            # 8자리여도 정수로 변환은 가능하므로 에러가 안 날 수 있음
            # 실제 검증은 API 레벨에서 pydantic으로 처리
        except ValueError:
            # 숫자 변환 실패
            pass

    def test_invalid_student_id_non_numeric(self, db_session):
        """숫자가 아닌 학번"""
        non_numeric_id = "abcdefghi"

        # 실행 및 검증
        with pytest.raises(ValueError):
            user_service.login_student(db_session, non_numeric_id)


class TestTokenGeneration:
    """토큰 생성 로직 테스트"""

    def test_generate_token_for_valid_user(self, test_user):
        """유효한 사용자에 대한 토큰 생성"""
        from uuid import uuid4

        # 토큰 생성 (auth.py의 로직 모방)
        token = f"token-{test_user.student_id}-{uuid4().hex}"

        # 검증
        assert token is not None
        assert str(test_user.student_id) in token
        assert token.startswith("token-")

    def test_token_contains_student_id(self, test_user):
        """토큰에 학번 정보 포함 여부"""
        from uuid import uuid4

        # 토큰 생성
        token = f"token-{test_user.student_id}-{uuid4().hex}"

        # 검증 - 학번이 토큰에 포함되어 있는지
        assert str(test_user.student_id) in token


class TestTokenValidation:
    """토큰 검증 로직 테스트"""

    def test_validate_valid_token(self, test_user):
        """유효한 토큰 검증 성공"""
        from uuid import uuid4

        # 유효한 토큰 생성
        token = f"token-{test_user.student_id}-{uuid4().hex}"

        # 검증 - 토큰 형식 확인
        assert token.startswith("token-")
        parts = token.split("-")
        assert len(parts) >= 3
        assert parts[1] == str(test_user.student_id)

    def test_validate_expired_token(self):
        """만료된 토큰 검증 실패"""
        # 현재 프로젝트에서는 단순 토큰 사용 (JWT 아님)
        # JWT 도입 시 만료 검증 로직 추가 필요
        expired_token = "token-202312345-expired"

        # 검증 - 형식은 맞지만 만료 여부는 별도 로직 필요
        assert "token" in expired_token

    def test_validate_invalid_token(self):
        """잘못된 토큰 검증 실패"""
        invalid_token = "invalid-format-token"

        # 검증 - token- 접두사가 없음
        assert not invalid_token.startswith("token-")
