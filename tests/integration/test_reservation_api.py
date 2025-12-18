"""
tests/integration/test_reservation_api.py - 예약 관리 API 통합 테스트
"""
import pytest
from tests.utils.assertions import ResponseAssertions


@pytest.mark.integration
@pytest.mark.reservation
class TestGetMyReservationsAPI:
    """내 예약 목록 조회 API 테스트"""

    def test_get_my_reservations_success(self, client, test_token, seat_reservation):
        """내 예약 목록 조회 성공 - 200 OK"""
        response = client.get(
            "/api/reservations/me",
            headers={"Authorization": f"Bearer {test_token}"}
        )

        ResponseAssertions.assert_success_response(response, status_code=200)
        data = response.json()
        assert "items" in data["payload"]
        assert len(data["payload"]["items"]) >= 1

    def test_get_my_reservations_empty(self, client, test_token):
        """예약이 없는 경우 빈 리스트 반환"""
        response = client.get(
            "/api/reservations/me",
            headers={"Authorization": f"Bearer {test_token}"}
        )

        ResponseAssertions.assert_success_response(response, status_code=200)
        data = response.json()
        assert data["payload"]["items"] == []

    def test_get_my_reservations_with_date_filter(self, client, test_token, seat_reservation):
        """날짜 필터링으로 예약 조회"""
        response = client.get(
            "/api/reservations/me?from=2025-12-20&to=2025-12-20",
            headers={"Authorization": f"Bearer {test_token}"}
        )

        ResponseAssertions.assert_success_response(response, status_code=200)
        data = response.json()
        # 필터링된 결과 검증
        for item in data["payload"]["items"]:
            assert item["date"] >= "2025-12-20"
            assert item["date"] <= "2025-12-20"

    def test_get_my_reservations_with_type_filter(self, client, test_token, seat_reservation, meeting_room_reservation):
        """타입 필터링으로 예약 조회 (meeting_room/seat)"""
        # 좌석만 필터링
        response = client.get(
            "/api/reservations/me?type=seat",
            headers={"Authorization": f"Bearer {test_token}"}
        )

        ResponseAssertions.assert_success_response(response, status_code=200)
        data = response.json()
        for item in data["payload"]["items"]:
            assert item["type"] == "seat"

    def test_get_my_reservations_response_format(self, client, test_token, seat_reservation):
        """응답 형식 검증 (items 배열)"""
        response = client.get(
            "/api/reservations/me",
            headers={"Authorization": f"Bearer {test_token}"}
        )

        ResponseAssertions.assert_success_response(response, status_code=200)
        ResponseAssertions.assert_payload_structure(
            response,
            expected_fields=["items"]
        )

    def test_get_my_reservations_item_fields(self, client, test_token, seat_reservation):
        """예약 아이템 필드 검증 (reservation_id, type, date 등)"""
        response = client.get(
            "/api/reservations/me",
            headers={"Authorization": f"Bearer {test_token}"}
        )

        data = response.json()
        if data["payload"]["items"]:
            item = data["payload"]["items"][0]
            assert "reservation_id" in item
            assert "type" in item
            assert "date" in item
            assert "start_time" in item
            assert "end_time" in item
            assert "status" in item


@pytest.mark.integration
@pytest.mark.reservation
class TestCancelReservationAPI:
    """예약 취소 API 테스트"""

    def test_cancel_reserved_reservation_success(self, client, test_token, seat_reservation):
        """RESERVED 상태 예약 취소 성공 - 200 OK"""
        response = client.delete(
            f"/api/reservations/me/{seat_reservation.reservation_id}",
            headers={"Authorization": f"Bearer {test_token}"}
        )

        ResponseAssertions.assert_success_response(response, status_code=200)
        data = response.json()
        assert data["payload"]["status"] == "CANCELED"

    def test_cancel_reservation_response_format(self, client, test_token, seat_reservation):
        """취소 응답 형식 검증"""
        response = client.delete(
            f"/api/reservations/me/{seat_reservation.reservation_id}",
            headers={"Authorization": f"Bearer {test_token}"}
        )

        ResponseAssertions.assert_payload_structure(
            response,
            expected_fields=["reservation_id", "type", "status"]
        )

    def test_cancel_reservation_contains_type_and_facility(self, client, test_token, seat_reservation):
        """취소 응답에 type, room_id/seat_id 포함"""
        response = client.delete(
            f"/api/reservations/me/{seat_reservation.reservation_id}",
            headers={"Authorization": f"Bearer {test_token}"}
        )

        data = response.json()
        payload = data["payload"]
        assert "type" in payload
        # 좌석 예약이므로 seat_id 있어야 함
        if payload["type"] == "seat":
            assert payload["seat_id"] is not None

    def test_cancel_already_canceled_reservation(self, client, test_token, canceled_reservation):
        """이미 취소된 예약 중복 취소 - 400 Bad Request"""
        response = client.delete(
            f"/api/reservations/me/{canceled_reservation.reservation_id}",
            headers={"Authorization": f"Bearer {test_token}"}
        )

        assert response.status_code == 400
        data = response.json()
        assert data["is_success"] is False

    def test_cancel_in_use_reservation(self, client, test_token, db_session):
        """IN_USE 상태 예약 취소 시도 - 403 Forbidden"""
        from app.models import Reservation, ReservationStatus
        from datetime import datetime, timezone

        # IN_USE 상태 예약 생성
        reservation = Reservation(
            student_id=202312345,
            seat_id=1,
            meeting_room_id=None,
            start_time=datetime(2025, 12, 20, 1, 0, 0, tzinfo=timezone.utc),
            end_time=datetime(2025, 12, 20, 3, 0, 0, tzinfo=timezone.utc),
            status=ReservationStatus.IN_USE
        )
        db_session.add(reservation)
        db_session.commit()
        db_session.refresh(reservation)

        response = client.delete(
            f"/api/reservations/me/{reservation.reservation_id}",
            headers={"Authorization": f"Bearer {test_token}"}
        )

        assert response.status_code == 403
        data = response.json()
        assert data["is_success"] is False

    def test_cancel_completed_reservation(self, client, test_token, expired_reservation):
        """COMPLETED 상태 예약 취소 시도 - 403 Forbidden"""
        response = client.delete(
            f"/api/reservations/me/{expired_reservation.reservation_id}",
            headers={"Authorization": f"Bearer {test_token}"}
        )

        assert response.status_code == 403
        data = response.json()
        assert data["is_success"] is False

    def test_cancel_other_user_reservation(self, client, test_token, db_session):
        """다른 사용자의 예약 취소 시도 - 403 Forbidden"""
        from app.models import Reservation, ReservationStatus
        from datetime import datetime, timezone

        # 다른 사용자의 예약 생성
        other_reservation = Reservation(
            student_id=999999999,  # 다른 사용자
            seat_id=1,
            meeting_room_id=None,
            start_time=datetime(2025, 12, 20, 1, 0, 0, tzinfo=timezone.utc),
            end_time=datetime(2025, 12, 20, 3, 0, 0, tzinfo=timezone.utc),
            status=ReservationStatus.RESERVED
        )
        db_session.add(other_reservation)
        db_session.commit()
        db_session.refresh(other_reservation)

        response = client.delete(
            f"/api/reservations/me/{other_reservation.reservation_id}",
            headers={"Authorization": f"Bearer {test_token}"}
        )

        assert response.status_code == 403
        data = response.json()
        assert data["is_success"] is False

    def test_cancel_nonexistent_reservation(self, client, test_token):
        """존재하지 않는 예약 취소 시도 - 400 Bad Request"""
        response = client.delete(
            "/api/reservations/me/999999",
            headers={"Authorization": f"Bearer {test_token}"}
        )

        assert response.status_code == 400
        data = response.json()
        assert data["is_success"] is False

    def test_cancel_without_authentication(self, client, seat_reservation):
        """인증 없이 예약 취소 시도 - 400 Bad Request"""
        response = client.delete(
            f"/api/reservations/me/{seat_reservation.reservation_id}"
        )

        assert response.status_code == 400


@pytest.mark.integration
@pytest.mark.reservation
@pytest.mark.meeting_room
class TestCancelMeetingRoomReservation:
    """회의실 예약 취소 테스트"""

    def test_cancel_meeting_room_reservation(self, client, test_token, meeting_room_reservation):
        """회의실 예약 취소 성공"""
        response = client.delete(
            f"/api/reservations/me/{meeting_room_reservation.reservation_id}",
            headers={"Authorization": f"Bearer {test_token}"}
        )

        ResponseAssertions.assert_success_response(response, status_code=200)
        data = response.json()
        assert data["payload"]["status"] == "CANCELED"
        assert data["payload"]["type"] == "meeting_room"

    def test_cancel_meeting_room_response_format(self, client, test_token, meeting_room_reservation):
        """회의실 예약 취소 응답 (type=meeting_room, room_id 포함)"""
        response = client.delete(
            f"/api/reservations/me/{meeting_room_reservation.reservation_id}",
            headers={"Authorization": f"Bearer {test_token}"}
        )

        data = response.json()
        payload = data["payload"]
        assert payload["type"] == "meeting_room"
        assert payload["room_id"] is not None
        assert payload["seat_id"] is None


@pytest.mark.integration
@pytest.mark.reservation
@pytest.mark.seat
class TestCancelSeatReservation:
    """좌석 예약 취소 테스트"""

    def test_cancel_seat_reservation(self, client, test_token, seat_reservation):
        """좌석 예약 취소 성공"""
        response = client.delete(
            f"/api/reservations/me/{seat_reservation.reservation_id}",
            headers={"Authorization": f"Bearer {test_token}"}
        )

        ResponseAssertions.assert_success_response(response, status_code=200)
        data = response.json()
        assert data["payload"]["status"] == "CANCELED"
        assert data["payload"]["type"] == "seat"

    def test_cancel_seat_response_format(self, client, test_token, seat_reservation):
        """좌석 예약 취소 응답 (type=seat, seat_id 포함)"""
        response = client.delete(
            f"/api/reservations/me/{seat_reservation.reservation_id}",
            headers={"Authorization": f"Bearer {test_token}"}
        )

        data = response.json()
        payload = data["payload"]
        assert payload["type"] == "seat"
        assert payload["seat_id"] is not None
        assert payload["room_id"] is None
