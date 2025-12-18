"""
tests/integration/test_auth_api.py - 인증 API 통합 테스트
"""
import pytest


class TestLoginAPI:
    """로그인 API 통합 테스트"""

    def test_login_success_with_valid_student_id(self, client):
        """유효한 학번으로 로그인 성공 - 200 OK"""
        pass

    def test_login_fail_with_blocked_student_id_202099999(self, client):
        """금지된 학번 202099999 - 401 Unauthorized"""
        pass

    def test_login_fail_with_blocked_student_id_202288888(self, client):
        """금지된 학번 202288888 - 401 Unauthorized"""
        pass

    def test_login_fail_with_invalid_format(self, client):
        """잘못된 형식의 학번 - 400 Bad Request"""
        pass

    def test_login_response_format(self, client):
        """로그인 성공 응답 형식 검증"""
        pass

    def test_login_response_contains_token(self, client):
        """로그인 응답에 access_token 포함"""
        pass

    def test_login_response_contains_student_id(self, client):
        """로그인 응답에 student_id 포함"""
        pass


class TestAuthenticationRequired:
    """인증 필요 엔드포인트 테스트"""

    def test_access_without_token(self, client):
        """토큰 없이 접근 시도 - 401 Unauthorized"""
        pass

    def test_access_with_invalid_token(self, client):
        """잘못된 토큰으로 접근 시도 - 401 Unauthorized"""
        pass

    def test_access_with_valid_token(self, client, test_token):
        """유효한 토큰으로 접근 - 200 OK"""
        pass
