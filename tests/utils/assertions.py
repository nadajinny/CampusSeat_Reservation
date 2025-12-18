"""
assertions.py - 커스텀 assertion 함수
"""


class ReservationAssertions:
    """예약 관련 검증 함수"""

    @staticmethod
    def assert_reservation_created(response, expected_type):
        """예약 생성 응답 검증"""
        pass

    @staticmethod
    def assert_reservation_canceled(response):
        """예약 취소 응답 검증"""
        pass

    @staticmethod
    def assert_time_conflict_error(response):
        """시간 충돌 에러 검증"""
        pass

    @staticmethod
    def assert_limit_exceeded_error(response, limit_type):
        """한도 초과 에러 검증 (daily/weekly)"""
        pass

    @staticmethod
    def assert_overlap_error(response):
        """시설 중복 예약 에러 검증"""
        pass


class ResponseAssertions:
    """API 응답 검증 함수"""

    @staticmethod
    def assert_success_response(response, status_code=200):
        """성공 응답 검증 (is_success=true, code=null)"""
        pass

    @staticmethod
    def assert_error_response(response, expected_code, status_code):
        """에러 응답 검증 (is_success=false, code=expected_code)"""
        pass

    @staticmethod
    def assert_error_code(response, expected_code):
        """에러 코드 검증"""
        pass

    @staticmethod
    def assert_payload_structure(response, expected_fields):
        """payload 구조 검증"""
        pass

    @staticmethod
    def assert_validation_error(response):
        """입력값 검증 에러 확인"""
        pass


class StatusAssertions:
    """상태 조회 관련 검증 함수"""

    @staticmethod
    def assert_slot_available(slot):
        """슬롯이 예약 가능함을 검증"""
        pass

    @staticmethod
    def assert_slot_unavailable(slot):
        """슬롯이 예약 불가능함을 검증"""
        pass

    @staticmethod
    def assert_operation_hours(payload, start="09:00", end="18:00"):
        """운영 시간 검증"""
        pass

    @staticmethod
    def assert_slot_count(slots, expected_count):
        """슬롯 개수 검증"""
        pass
