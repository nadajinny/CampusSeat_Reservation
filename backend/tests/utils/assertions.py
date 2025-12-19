"""
assertions.py - 커스텀 assertion 함수
"""


class ReservationAssertions:
    """예약 관련 검증 함수"""

    @staticmethod
    def assert_reservation_created(response, expected_type):
        """예약 생성 응답 검증"""
        assert response.status_code == 201, f"Expected 201, got {response.status_code}"
        data = response.json()
        assert data["is_success"] is True
        assert "payload" in data
        assert "reservation_id" in data["payload"]
        assert data["payload"]["type"] == expected_type

        if expected_type == "seat":
            assert "seat_id" in data["payload"]
        elif expected_type == "meeting_room":
            assert "room_id" in data["payload"]

    @staticmethod
    def assert_reservation_canceled(response):
        """예약 취소 응답 검증"""
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data["is_success"] is True
        assert "payload" in data
        assert data["payload"]["status"] == "CANCELED"

    @staticmethod
    def assert_time_conflict_error(response):
        """시간 충돌 에러 검증"""
        assert response.status_code == 409, f"Expected 409, got {response.status_code}"
        data = response.json()
        assert data["is_success"] is False
        assert data["code"] in ["RESERVATION_TIME_CONFLICT", "RESERVATION_CONFLICT"]

    @staticmethod
    def assert_limit_exceeded_error(response, limit_type):
        """한도 초과 에러 검증 (daily/weekly)"""
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        data = response.json()
        assert data["is_success"] is False
        if limit_type == "daily":
            assert "DAILY" in data["code"] or "일일" in data["message"]
        elif limit_type == "weekly":
            assert "WEEKLY" in data["code"] or "주간" in data["message"]

    @staticmethod
    def assert_overlap_error(response):
        """시설 중복 예약 에러 검증"""
        assert response.status_code == 409, f"Expected 409, got {response.status_code}"
        data = response.json()
        assert data["is_success"] is False
        assert "OVERLAP" in data["code"] or "중복" in data["message"]


class ResponseAssertions:
    """API 응답 검증 함수"""

    @staticmethod
    def assert_success_response(response, status_code=200):
        """성공 응답 검증 (is_success=true, code=null)"""
        assert response.status_code == status_code, f"Expected {status_code}, got {response.status_code}"
        data = response.json()
        assert data["is_success"] is True
        assert data["code"] is None
        assert "payload" in data

    @staticmethod
    def assert_error_response(response, expected_code, status_code):
        """에러 응답 검증 (is_success=false, code=expected_code)"""
        assert response.status_code == status_code, f"Expected {status_code}, got {response.status_code}"
        data = response.json()
        assert data["is_success"] is False
        assert data["code"] == expected_code
        assert "message" in data

    @staticmethod
    def assert_error_code(response, expected_code):
        """에러 코드 검증"""
        data = response.json()
        assert data["is_success"] is False
        assert data["code"] == expected_code

    @staticmethod
    def assert_payload_structure(response, expected_fields):
        """payload 구조 검증"""
        data = response.json()
        assert "payload" in data
        payload = data["payload"]

        for field in expected_fields:
            assert field in payload, f"Expected field '{field}' not found in payload"

    @staticmethod
    def assert_validation_error(response):
        """입력값 검증 에러 확인"""
        assert response.status_code == 422, f"Expected 422, got {response.status_code}"
        data = response.json()
        assert "detail" in data  # FastAPI validation error format


class StatusAssertions:
    """상태 조회 관련 검증 함수"""

    @staticmethod
    def assert_slot_available(slot):
        """슬롯이 예약 가능함을 검증"""
        assert slot["is_available"] is True, f"Expected slot to be available, but it's not"
        assert "start_time" in slot
        assert "end_time" in slot

    @staticmethod
    def assert_slot_unavailable(slot):
        """슬롯이 예약 불가능함을 검증"""
        assert slot["is_available"] is False, f"Expected slot to be unavailable, but it's available"

    @staticmethod
    def assert_operation_hours(payload, start="09:00", end="18:00"):
        """운영 시간 검증"""
        assert "operation_hours" in payload
        hours = payload["operation_hours"]
        assert hours["start"] == start
        assert hours["end"] == end

    @staticmethod
    def assert_slot_count(slots, expected_count):
        """슬롯 개수 검증"""
        assert len(slots) == expected_count, f"Expected {expected_count} slots, got {len(slots)}"
