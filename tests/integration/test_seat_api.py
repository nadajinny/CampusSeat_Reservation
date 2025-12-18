"""
tests/integration/test_seat_api.py - 좌석 예약 API 통합 테스트
"""
import pytest
from datetime import date, timedelta
from tests.utils.assertions import ResponseAssertions, ReservationAssertions


def get_tomorrow():
    return (date.today() + timedelta(days=1)).isoformat()


def get_auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.integration
@pytest.mark.seat
class TestCreateSeatReservationAPI:
    """좌석 예약 생성 API 테스트"""

    def test_create_seat_reservation_success(self, client, test_token, test_seat):
        """좌석 예약 생성 성공 - 201 Created"""
        tomorrow = get_tomorrow()
        response = client.post(
            "/api/reservations/seats",
            headers=get_auth_headers(test_token),
            json={
                "date": tomorrow,
                "start_time": "10:00",
                "end_time": "12:00",
                "seat_id": test_seat.seat_id
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["is_success"] is True
        assert data["payload"]["seat_id"] == test_seat.seat_id
        assert data["payload"]["status"] == "RESERVED"

    def test_create_seat_reservation_response_format(self, client, test_token, test_seat):
        """예약 생성 응답 형식 검증"""
        tomorrow = get_tomorrow()
        response = client.post(
            "/api/reservations/seats",
            headers=get_auth_headers(test_token),
            json={
                "date": tomorrow,
                "start_time": "10:00",
                "end_time": "12:00",
                "seat_id": test_seat.seat_id
            }
        )

        data = response.json()
        payload = data["payload"]
        assert "reservation_id" in payload
        assert "seat_id" in payload
        assert "date" in payload
        assert "start_time" in payload
        assert "end_time" in payload
        assert "status" in payload
        assert payload["type"] == "seat"

    def test_create_seat_reservation_without_auth(self, client, test_seat):
        """인증 없이 예약 시도 - 400 Bad Request"""
        tomorrow = get_tomorrow()
        response = client.post(
            "/api/reservations/seats",
            json={
                "date": tomorrow,
                "start_time": "10:00",
                "end_time": "12:00",
                "seat_id": test_seat.seat_id
            }
        )

        assert response.status_code == 400


@pytest.mark.integration
@pytest.mark.seat
class TestRandomSeatReservationAPI:
    """랜덤 좌석 예약 API 테스트"""

    def test_random_seat_reservation_success(self, client, test_token, available_seats):
        """랜덤 좌석 예약 성공 - 201 Created"""
        tomorrow = get_tomorrow()
        response = client.post(
            "/api/reservations/seats/random",
            headers=get_auth_headers(test_token),
            json={
                "date": tomorrow,
                "start_time": "10:00",
                "end_time": "12:00"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["is_success"] is True
        assert data["payload"]["seat_id"] is not None
        assert data["payload"]["status"] == "RESERVED"

    def test_random_seat_assigned_from_available(self, client, test_token, available_seats):
        """랜덤 배정된 좌석이 가용 좌석 중 하나인지 확인"""
        tomorrow = get_tomorrow()
        response = client.post(
            "/api/reservations/seats/random",
            headers=get_auth_headers(test_token),
            json={
                "date": tomorrow,
                "start_time": "10:00",
                "end_time": "12:00"
            }
        )

        data = response.json()
        assigned_seat_id = data["payload"]["seat_id"]
        available_seat_ids = [s.seat_id for s in available_seats]

        assert assigned_seat_id in available_seat_ids


@pytest.mark.integration
@pytest.mark.seat
class TestSeatTimeConflictAPI:
    """좌석 시간 충돌 API 테스트"""

    def test_same_seat_same_time_conflict(self, client, test_token, test_seat, multiple_users):
        """같은 좌석, 같은 시간 예약 → 409 Conflict"""
        tomorrow = get_tomorrow()

        # 첫 번째 예약
        response1 = client.post(
            "/api/reservations/seats",
            headers=get_auth_headers(test_token),
            json={
                "date": tomorrow,
                "start_time": "10:00",
                "end_time": "12:00",
                "seat_id": test_seat.seat_id
            }
        )
        assert response1.status_code == 201

        # 다른 사용자 토큰 생성
        from uuid import uuid4
        other_token = f"token-{multiple_users[0].student_id}-{uuid4().hex}"

        # 같은 좌석, 같은 시간 예약 시도
        response2 = client.post(
            "/api/reservations/seats",
            headers=get_auth_headers(other_token),
            json={
                "date": tomorrow,
                "start_time": "10:00",
                "end_time": "12:00",
                "seat_id": test_seat.seat_id
            }
        )

        assert response2.status_code == 409
        data = response2.json()
        assert data["is_success"] is False
        assert data["code"] == "RESERVATION_CONFLICT"

    def test_same_seat_different_time_success(self, client, test_token, test_seat, multiple_users):
        """같은 좌석, 다른 시간 예약 → 성공"""
        tomorrow = get_tomorrow()

        # 첫 번째 예약
        response1 = client.post(
            "/api/reservations/seats",
            headers=get_auth_headers(test_token),
            json={
                "date": tomorrow,
                "start_time": "10:00",
                "end_time": "12:00",
                "seat_id": test_seat.seat_id
            }
        )
        assert response1.status_code == 201

        # 다른 사용자 토큰
        from uuid import uuid4
        other_token = f"token-{multiple_users[0].student_id}-{uuid4().hex}"

        # 같은 좌석, 다른 시간
        response2 = client.post(
            "/api/reservations/seats",
            headers=get_auth_headers(other_token),
            json={
                "date": tomorrow,
                "start_time": "14:00",
                "end_time": "16:00",
                "seat_id": test_seat.seat_id
            }
        )

        assert response2.status_code == 201


@pytest.mark.integration
@pytest.mark.seat
class TestSeatDailyLimitAPI:
    """좌석 일일 한도 API 테스트"""

    def test_daily_limit_exceeded(self, client, test_token, available_seats):
        """일일 한도(240분) 초과 시 400 에러"""
        tomorrow = get_tomorrow()

        # 첫 번째 예약 (120분)
        response1 = client.post(
            "/api/reservations/seats",
            headers=get_auth_headers(test_token),
            json={
                "date": tomorrow,
                "start_time": "10:00",
                "end_time": "12:00",
                "seat_id": available_seats[0].seat_id
            }
        )
        assert response1.status_code == 201

        # 두 번째 예약 (120분) → 총 240분
        response2 = client.post(
            "/api/reservations/seats",
            headers=get_auth_headers(test_token),
            json={
                "date": tomorrow,
                "start_time": "14:00",
                "end_time": "16:00",
                "seat_id": available_seats[1].seat_id
            }
        )
        assert response2.status_code == 201

        # 세 번째 예약 시도 (120분) → 총 360분, 한도 초과
        response3 = client.post(
            "/api/reservations/seats",
            headers=get_auth_headers(test_token),
            json={
                "date": tomorrow,
                "start_time": "16:00",
                "end_time": "18:00",
                "seat_id": available_seats[2].seat_id
            }
        )

        assert response3.status_code == 400
        data = response3.json()
        assert data["is_success"] is False
        assert data["code"] == "DAILY_LIMIT_EXCEEDED"


@pytest.mark.integration
@pytest.mark.seat
class TestSeatOverlapAPI:
    """좌석 중복 예약 API 테스트"""

    def test_overlap_with_own_seat_reservation(self, client, test_token, available_seats):
        """같은 시간대 본인 좌석 예약 존재 시 중복 에러"""
        tomorrow = get_tomorrow()

        # 첫 번째 좌석 예약
        response1 = client.post(
            "/api/reservations/seats",
            headers=get_auth_headers(test_token),
            json={
                "date": tomorrow,
                "start_time": "10:00",
                "end_time": "12:00",
                "seat_id": available_seats[0].seat_id
            }
        )
        assert response1.status_code == 201

        # 같은 시간대 다른 좌석 예약 시도
        response2 = client.post(
            "/api/reservations/seats",
            headers=get_auth_headers(test_token),
            json={
                "date": tomorrow,
                "start_time": "10:00",
                "end_time": "12:00",
                "seat_id": available_seats[1].seat_id
            }
        )

        assert response2.status_code == 409
        data = response2.json()
        assert data["is_success"] is False
        assert data["code"] == "OVERLAP_WITH_OTHER_FACILITY"


@pytest.mark.integration
@pytest.mark.seat
class TestSeatValidationAPI:
    """좌석 예약 입력값 검증 API 테스트"""

    def test_invalid_time_range(self, client, test_token, test_seat):
        """종료 시간이 시작 시간보다 빠름 → 400 에러"""
        tomorrow = get_tomorrow()
        response = client.post(
            "/api/reservations/seats",
            headers=get_auth_headers(test_token),
            json={
                "date": tomorrow,
                "start_time": "14:00",
                "end_time": "12:00",  # 잘못된 시간
                "seat_id": test_seat.seat_id
            }
        )

        assert response.status_code == 400

    def test_not_2hour_duration(self, client, test_token, test_seat):
        """2시간 단위가 아닌 예약 → 400 에러"""
        tomorrow = get_tomorrow()
        response = client.post(
            "/api/reservations/seats",
            headers=get_auth_headers(test_token),
            json={
                "date": tomorrow,
                "start_time": "10:00",
                "end_time": "11:00",  # 1시간만
                "seat_id": test_seat.seat_id
            }
        )

        assert response.status_code == 400

    def test_outside_operation_hours(self, client, test_token, test_seat):
        """운영 시간 외 예약 → 400 에러"""
        tomorrow = get_tomorrow()
        response = client.post(
            "/api/reservations/seats",
            headers=get_auth_headers(test_token),
            json={
                "date": tomorrow,
                "start_time": "07:00",  # 운영 시간 전
                "end_time": "09:00",
                "seat_id": test_seat.seat_id
            }
        )

        assert response.status_code == 400

    def test_past_date_reservation(self, client, test_token, test_seat):
        """과거 날짜 예약 → 400 에러"""
        past_date = (date.today() - timedelta(days=1)).isoformat()
        response = client.post(
            "/api/reservations/seats",
            headers=get_auth_headers(test_token),
            json={
                "date": past_date,
                "start_time": "10:00",
                "end_time": "12:00",
                "seat_id": test_seat.seat_id
            }
        )

        assert response.status_code == 400


@pytest.mark.integration
@pytest.mark.seat
class TestSeatListAPI:
    """좌석 목록 조회 API 테스트"""

    def test_get_all_seats(self, client, available_seats):
        """전체 좌석 목록 조회"""
        response = client.get("/seats")

        assert response.status_code == 200
        data = response.json()
        assert data["is_success"] is True
        assert len(data["payload"]) >= len(available_seats)

    def test_get_single_seat(self, client, test_seat):
        """특정 좌석 조회"""
        response = client.get(f"/seats/{test_seat.seat_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["is_success"] is True
        assert data["payload"]["seat_id"] == test_seat.seat_id

    def test_get_nonexistent_seat(self, client):
        """존재하지 않는 좌석 조회 → 400"""
        response = client.get("/seats/99999")

        assert response.status_code == 400
        data = response.json()
        assert data["is_success"] is False
        assert data["code"] == "NOT_FOUND"
