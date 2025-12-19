"""
tests/integration/test_status_api.py - 상태 조회 API 통합 테스트
"""
import pytest
from tests.utils.assertions import ResponseAssertions, StatusAssertions


@pytest.mark.integration
@pytest.mark.status
@pytest.mark.meeting_room
class TestGetMeetingRoomStatusAPI:
    """회의실 예약 현황 조회 API 테스트"""

    def test_get_meeting_room_status_success(self, client, available_meeting_rooms):
        """회의실 현황 조회 성공 - 200 OK"""
        response = client.get("/api/status/meeting-rooms?date=2025-12-20")

        ResponseAssertions.assert_success_response(response, status_code=200)

    def test_get_meeting_room_status_response_format(self, client, available_meeting_rooms):
        """응답 형식 검증 (date, operation_hours, rooms)"""
        response = client.get("/api/status/meeting-rooms?date=2025-12-20")

        ResponseAssertions.assert_payload_structure(
            response,
            expected_fields=["date", "operation_hours", "rooms"]
        )

    def test_get_meeting_room_status_room_count(self, client, available_meeting_rooms):
        """회의실 여러 개 반환 확인"""
        response = client.get("/api/status/meeting-rooms?date=2025-12-20")

        data = response.json()
        # available_meeting_rooms가 5개 생성하므로
        assert len(data["payload"]["rooms"]) >= 3

    def test_get_meeting_room_status_slot_count(self, client, available_meeting_rooms):
        """1시간 단위 슬롯 개수 확인"""
        response = client.get("/api/status/meeting-rooms?date=2025-12-20")

        data = response.json()
        if data["payload"]["rooms"]:
            first_room = data["payload"]["rooms"][0]
            # 슬롯이 있는지 확인
            assert len(first_room["slots"]) > 0

    def test_get_meeting_room_status_slot_format(self, client, available_meeting_rooms):
        """슬롯 형식 검증 (start, end, is_available)"""
        response = client.get("/api/status/meeting-rooms?date=2025-12-20")

        data = response.json()
        if data["payload"]["rooms"]:
            first_slot = data["payload"]["rooms"][0]["slots"][0]
            assert "start" in first_slot
            assert "end" in first_slot
            assert "is_available" in first_slot

    def test_get_meeting_room_status_with_reservation(self, client, available_meeting_rooms, meeting_room_reservation):
        """예약된 슬롯은 is_available=false"""
        response = client.get("/api/status/meeting-rooms?date=2025-12-20")

        data = response.json()
        # 예약이 있는 회의실의 일부 슬롯은 사용 불가
        has_unavailable_slot = False
        for room in data["payload"]["rooms"]:
            for slot in room["slots"]:
                if not slot["is_available"]:
                    has_unavailable_slot = True
                    break

        assert has_unavailable_slot

    def test_get_meeting_room_status_without_reservation(self, client, available_meeting_rooms):
        """예약 없는 슬롯은 is_available=true"""
        response = client.get("/api/status/meeting-rooms?date=2025-12-25")

        data = response.json()
        # 예약이 없는 날짜이므로 모든 슬롯 사용 가능
        for room in data["payload"]["rooms"]:
            for slot in room["slots"]:
                assert slot["is_available"] is True

    def test_get_meeting_room_status_canceled_reservation_available(self, client, available_meeting_rooms, canceled_reservation):
        """취소된 예약은 is_available=true"""
        # canceled_reservation은 2025-12-21 날짜
        response = client.get("/api/status/meeting-rooms?date=2025-12-21")

        data = response.json()
        # 취소된 예약이므로 모든 슬롯 사용 가능해야 함
        for room in data["payload"]["rooms"]:
            for slot in room["slots"]:
                # 취소된 예약 시간대도 사용 가능
                assert slot["is_available"] is True


@pytest.mark.integration
@pytest.mark.status
@pytest.mark.seat
class TestGetSeatStatusAPI:
    """좌석 예약 현황 조회 API 테스트"""

    def test_get_seat_status_success(self, client, available_seats):
        """좌석 현황 조회 성공 - 200 OK"""
        response = client.get("/api/status/seats?date=2025-12-20")

        ResponseAssertions.assert_success_response(response, status_code=200)

    def test_get_seat_status_response_format(self, client, available_seats):
        """응답 형식 검증 (date, operation_hours, seats)"""
        response = client.get("/api/status/seats?date=2025-12-20")

        ResponseAssertions.assert_payload_structure(
            response,
            expected_fields=["date", "operation_hours", "seats"]
        )

    def test_get_seat_status_seat_count(self, client, available_seats):
        """좌석 여러 개 반환 확인"""
        response = client.get("/api/status/seats?date=2025-12-20")

        data = response.json()
        # available_seats가 10개 생성하므로
        assert len(data["payload"]["seats"]) >= 10

    def test_get_seat_status_slot_count(self, client, available_seats):
        """슬롯 개수 확인"""
        response = client.get("/api/status/seats?date=2025-12-20")

        data = response.json()
        if data["payload"]["seats"]:
            first_seat = data["payload"]["seats"][0]
            # 슬롯이 있는지 확인
            assert len(first_seat["slots"]) > 0

    def test_get_seat_status_slot_format(self, client, available_seats):
        """슬롯 형식 검증 (start, end, is_available)"""
        response = client.get("/api/status/seats?date=2025-12-20")

        data = response.json()
        if data["payload"]["seats"]:
            first_slot = data["payload"]["seats"][0]["slots"][0]
            assert "start" in first_slot
            assert "end" in first_slot
            assert "is_available" in first_slot

    def test_get_seat_status_slots(self, client, available_seats):
        """권장 슬롯 시간대 확인"""
        response = client.get("/api/status/seats?date=2025-12-20")

        data = response.json()
        if data["payload"]["seats"]:
            slots = data["payload"]["seats"][0]["slots"]
            # 각 슬롯은 2시간 단위
            for slot in slots:
                assert slot["start"] is not None
                assert slot["end"] is not None

    def test_get_seat_status_with_reservation(self, client, available_seats, seat_reservation):
        """예약된 슬롯은 is_available=false"""
        response = client.get("/api/status/seats?date=2025-12-20")

        data = response.json()
        # 예약이 있는 좌석의 일부 슬롯은 사용 불가
        has_unavailable_slot = False
        for seat in data["payload"]["seats"]:
            for slot in seat["slots"]:
                if not slot["is_available"]:
                    has_unavailable_slot = True
                    break

        assert has_unavailable_slot

    def test_get_seat_status_without_reservation(self, client, available_seats):
        """예약 없는 슬롯은 is_available=true"""
        response = client.get("/api/status/seats?date=2025-12-25")

        data = response.json()
        # 예약이 없는 날짜이므로 모든 슬롯 사용 가능
        for seat in data["payload"]["seats"]:
            for slot in seat["slots"]:
                assert slot["is_available"] is True

    def test_get_seat_status_canceled_reservation_available(self, client, available_seats, canceled_reservation):
        """취소된 예약은 is_available=true"""
        # canceled_reservation은 2025-12-21 날짜
        response = client.get("/api/status/seats?date=2025-12-21")

        data = response.json()
        # 취소된 예약이므로 모든 슬롯 사용 가능해야 함
        for seat in data["payload"]["seats"]:
            for slot in seat["slots"]:
                # 취소된 예약 시간대도 사용 가능
                assert slot["is_available"] is True


@pytest.mark.integration
@pytest.mark.status
class TestStatusQueryParameters:
    """상태 조회 쿼리 파라미터 테스트"""

    def test_meeting_room_status_without_date_parameter(self, client, available_meeting_rooms):
        """date 파라미터 없이 요청 - 400 Bad Request"""
        response = client.get("/api/status/meeting-rooms")

        # FastAPI validation error
        assert response.status_code == 400

    def test_seat_status_without_date_parameter(self, client, available_seats):
        """date 파라미터 없이 요청 - 400 Bad Request"""
        response = client.get("/api/status/seats")

        # FastAPI validation error
        assert response.status_code == 400

    def test_status_with_invalid_date_format(self, client, available_meeting_rooms):
        """잘못된 날짜 형식 - 400 Bad Request"""
        response = client.get("/api/status/meeting-rooms?date=20-12-2025")

        # FastAPI validation error
        assert response.status_code == 400

    def test_status_with_valid_date_format(self, client, available_meeting_rooms):
        """올바른 날짜 형식 (YYYY-MM-DD) - 200 OK"""
        response = client.get("/api/status/meeting-rooms?date=2025-12-20")

        assert response.status_code == 200
        data = response.json()
        assert data["is_success"] is True
