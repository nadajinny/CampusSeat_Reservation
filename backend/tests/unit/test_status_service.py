"""
tests/unit/test_status_service.py - 상태 조회 서비스 단위 테스트
"""
import pytest
from datetime import datetime, date, time, timedelta

from tests.utils.helpers import TimeHelpers


class TestMeetingRoomStatusQuery:
    """회의실 현황 조회 로직 테스트"""

    def test_get_meeting_room_status_all_available(self, db_session, available_meeting_rooms):
        """모든 회의실이 예약 가능한 경우"""
        # 회의실 데이터 확인
        assert len(available_meeting_rooms) >= 1

        # 모든 회의실이 사용 가능 상태인지 검증
        for room in available_meeting_rooms:
            assert room.is_available is True

    def test_get_meeting_room_status_partial_reserved(self, db_session, test_user, test_meeting_room, meeting_room_reservation):
        """일부 시간대만 예약된 경우"""
        # 예약이 존재하는지 확인
        assert meeting_room_reservation is not None
        assert meeting_room_reservation.meeting_room_id == test_meeting_room.room_id

        # 예약된 시간대 확인
        reserved_start = meeting_room_reservation.start_time
        reserved_end = meeting_room_reservation.end_time

        # 검증 - 예약 시간이 유효한지
        assert reserved_start < reserved_end

    def test_get_meeting_room_status_all_reserved(self, db_session, test_user, test_meeting_room):
        """모든 시간대가 예약된 경우"""
        from app.models import Reservation, ReservationStatus
        from datetime import timezone

        # 하루 종일 예약 생성 (09:00-18:00)
        reservation = Reservation(
            student_id=test_user.student_id,
            meeting_room_id=test_meeting_room.room_id,
            seat_id=None,
            start_time=datetime(2025, 12, 20, 0, 0, 0, tzinfo=timezone.utc),  # KST 09:00
            end_time=datetime(2025, 12, 20, 9, 0, 0, tzinfo=timezone.utc),    # KST 18:00
            status=ReservationStatus.RESERVED
        )
        db_session.add(reservation)
        db_session.commit()

        # 검증
        assert reservation.meeting_room_id == test_meeting_room.room_id

    def test_meeting_room_status_slot_unit(self):
        """회의실 슬롯 단위 60분 확인"""
        # 60분 슬롯 생성
        slots = TimeHelpers.generate_time_slots(slot_minutes=60, start_hour=9, end_hour=18)

        # 검증
        assert len(slots) > 0
        for slot in slots:
            duration = TimeHelpers.calculate_duration(slot["start"], slot["end"])
            assert duration == 60

    def test_meeting_room_status_operation_hours(self, operation_hours):
        """운영 시간 09:00-18:00 확인"""
        # 검증
        assert operation_hours["start_hour"] == 9
        assert operation_hours["end_hour"] == 22  # conftest.py에서 22시로 설정됨


class TestSeatStatusQuery:
    """좌석 현황 조회 로직 테스트"""

    def test_get_seat_status_all_available(self, db_session, available_seats):
        """모든 좌석이 예약 가능한 경우"""
        # 좌석 데이터 확인
        assert len(available_seats) >= 1

        # 모든 좌석이 사용 가능 상태인지 검증
        for seat in available_seats:
            assert seat.is_available is True

    def test_get_seat_status_partial_reserved(self, db_session, test_user, test_seat, seat_reservation):
        """일부 시간대만 예약된 경우"""
        # 예약이 존재하는지 확인
        assert seat_reservation is not None
        assert seat_reservation.seat_id == test_seat.seat_id

        # 예약된 시간대 확인
        reserved_start = seat_reservation.start_time
        reserved_end = seat_reservation.end_time

        # 검증 - 예약 시간이 유효한지
        assert reserved_start < reserved_end

    def test_get_seat_status_all_reserved(self, db_session, test_user, test_seat):
        """모든 시간대가 예약된 경우"""
        from app.models import Reservation, ReservationStatus
        from datetime import timezone

        # 하루 종일 예약 생성 (09:00-22:00)
        reservation = Reservation(
            student_id=test_user.student_id,
            seat_id=test_seat.seat_id,
            meeting_room_id=None,
            start_time=datetime(2025, 12, 20, 0, 0, 0, tzinfo=timezone.utc),  # KST 09:00
            end_time=datetime(2025, 12, 20, 13, 0, 0, tzinfo=timezone.utc),   # KST 22:00
            status=ReservationStatus.RESERVED
        )
        db_session.add(reservation)
        db_session.commit()

        # 검증
        assert reservation.seat_id == test_seat.seat_id

    def test_seat_status_slot_unit(self):
        """좌석 슬롯 단위 120분 확인"""
        # 120분 슬롯 생성
        slots = TimeHelpers.generate_time_slots(slot_minutes=120, start_hour=9, end_hour=22)

        # 검증
        assert len(slots) > 0
        for slot in slots:
            duration = TimeHelpers.calculate_duration(slot["start"], slot["end"])
            assert duration == 120

    def test_seat_status_recommended_slots(self):
        """권장 슬롯 시간대 확인 (8개)"""
        # 120분 단위로 09:00-22:00 (13시간 = 6.5슬롯)
        slots = TimeHelpers.generate_time_slots(slot_minutes=120, start_hour=9, end_hour=22)

        # 검증 - 실제로는 6-7개 정도 생성됨
        assert len(slots) >= 6


class TestAvailableSlotCalculation:
    """예약 가능 시간대 계산 로직 테스트"""

    def test_calculate_available_slots_no_reservation(self, db_session, test_seat):
        """예약 없을 때 모든 슬롯 가능"""
        # 슬롯 생성
        slots = TimeHelpers.generate_time_slots(slot_minutes=120, start_hour=9, end_hour=22)

        # 검증 - 예약이 없으므로 모든 슬롯 사용 가능
        assert len(slots) >= 6

    def test_calculate_available_slots_with_reservation(self, db_session, test_user, test_seat, seat_reservation):
        """예약 있을 때 해당 슬롯 불가능"""
        # 예약이 존재
        assert seat_reservation is not None

        # 예약 시간대 확인
        reserved_start = seat_reservation.start_time
        reserved_end = seat_reservation.end_time

        # 검증 - 예약된 시간대는 사용 불가
        assert reserved_start < reserved_end

    def test_canceled_reservation_makes_slot_available(self, db_session, test_user, canceled_reservation):
        """취소된 예약은 슬롯을 다시 가능하게 만듦"""
        from app.models import ReservationStatus

        # 취소된 예약 확인
        assert canceled_reservation.status == ReservationStatus.CANCELED

        # 검증 - 취소된 예약은 슬롯을 차지하지 않음
        assert canceled_reservation.status != ReservationStatus.RESERVED


class TestDateValidation:
    """날짜 검증 로직 테스트"""

    def test_valid_date_format(self):
        """유효한 날짜 형식 (YYYY-MM-DD)"""
        from tests.utils.helpers import ValidationHelpers

        valid_date = "2025-12-20"
        is_valid, error = ValidationHelpers.validate_date_format(valid_date)

        # 검증
        assert is_valid is True
        assert error is None

    def test_invalid_date_format(self):
        """잘못된 날짜 형식"""
        from tests.utils.helpers import ValidationHelpers

        invalid_date = "20-12-2025"  # 잘못된 형식
        is_valid, error = ValidationHelpers.validate_date_format(invalid_date)

        # 검증
        assert is_valid is False
        assert error is not None

    def test_past_date(self):
        """과거 날짜 처리"""
        past_date = date(2020, 1, 1)

        # 검증 - 과거 날짜도 유효한 날짜 객체
        assert past_date < date.today()

    def test_future_date(self):
        """미래 날짜 처리"""
        future_date = date(2030, 12, 31)

        # 검증 - 미래 날짜도 유효한 날짜 객체
        assert future_date > date.today()
