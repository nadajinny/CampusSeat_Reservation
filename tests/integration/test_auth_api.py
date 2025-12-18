"""
tests/integration/test_auth_api.py - 인증 API 통합 테스트
"""
import pytest


def login(client, student_id: str = "202312345"):
    """로그인 헬퍼"""
    return client.post("/api/auth/login", json={"student_id": student_id})


class TestLoginAPI:
    """로그인 API 통합 테스트"""

    def test_login_success_with_valid_student_id(self, client):
        # 정상 학번 로그인 성공 및 기본 응답 구조 검증
        resp = login(client, "202312345")
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_success"] is True
        assert data["code"] is None
        assert "access_token" in data["payload"]
        assert data["payload"]["student_id"] == 202312345

    @pytest.mark.parametrize("blocked_id", ["202099999", "202288888"])
    def test_login_fail_with_blocked_student_id(self, client, blocked_id):
        # 금지 학번 로그인 시도 시 거부
        resp = login(client, blocked_id)
        assert resp.status_code == 400  # BusinessException 기본 400
        data = resp.json()
        assert data["is_success"] is False
        assert data["code"] == "AUTH_INVALID_STUDENT_ID"

    def test_login_fail_with_invalid_format(self, client):
        # 9자리 숫자 형식이 아니면 검증 실패
        resp = login(client, "12345")  # 9자리 숫자 아님
        assert resp.status_code == 400
        data = resp.json()
        assert data["is_success"] is False
        assert data["code"] == "VALIDATION_ERROR"

    def test_login_response_contains_token_and_student_id(self, client):
        # 로그인 응답에 토큰/학번 필수 필드 포함 여부 확인
        resp = login(client, "202312345")
        data = resp.json()
        assert set(data.keys()) == {"is_success", "code", "payload"}
        assert {"access_token", "student_id"}.issubset(data["payload"].keys())
        assert data["payload"]["access_token"].startswith("token-")
        assert data["payload"]["student_id"] == 202312345


class TestAuthenticationRequired:
    """인증 필요 엔드포인트 테스트"""

    def test_access_without_token(self, client):
        # 토큰 없이 보호된 엔드포인트 접근 시 거부
        resp = client.get("/api/reservations/me")
        assert resp.status_code == 400  # AUTH_UNAUTHORIZED -> 400
        data = resp.json()
        assert data["is_success"] is False
        assert data["code"] == "AUTH_UNAUTHORIZED"

    def test_access_with_invalid_token(self, client):
        # 잘못된 토큰으로 접근 시 거부
        resp = client.get(
            "/api/reservations/me",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert resp.status_code == 400
        data = resp.json()
        assert data["is_success"] is False
        assert data["code"] == "AUTH_UNAUTHORIZED"

    def test_access_with_valid_token(self, client):
        # 로그인 후 받은 토큰으로 접근 시 성공
        login_resp = login(client, "202312345")
        token = login_resp.json()["payload"]["access_token"]

        resp = client.get(
            "/api/reservations/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_success"] is True
