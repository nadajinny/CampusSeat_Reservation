"""
tests/unit/test_seat_service.py - 좌석 예약 서비스 단위 테스트
"""
import pytest
from datetime import datetime, date, time, timedelta, timezone

from app.services import seat_service
from app.schemas.seat import SeatReservationCreate
from app.models import ReservationStatus, Reservation, Seat
from app.constants import ErrorCode, ReservationLimits
from app.exceptions import BusinessException, ConflictException, LimitExceededException


KST = timezone(timedelta(hours=9))
UTC = timezone.utc

# 내일 날짜 (테스트용)
def get_tomorrow():
    return date.today() + timedelta(days=1)


class TestSeatQuery:
    """좌석 조회 로직 테스트"""

    def test_get_seat_by_id(self, db_session, test_seat):
        """좌석 ID로 조회"""
        seat = seat_service.get_seat(db_session, test_seat.seat_id)

        assert seat is not None
        assert seat.seat_id == test_seat.seat_id

    def test_get_nonexistent_seat(self, db_session):
        """존재하지 않는 좌석 조회 → None"""
        seat = seat_service.get_seat(db_session, 99999)

        assert seat is None

    def test_get_all_seats(self, db_session, available_seats):
        """전체 좌석 목록 조회"""
        seats = seat_service.get_all_seats(db_session)

        assert len(seats) >= len(available_seats)

    def test_get_seats_count(self, db_session, available_seats):
        """좌석 총 개수 조회"""
        count = seat_service.get_seats_count(db_session)

        assert count >= len(available_seats)


class TestSeatReservationCreation:
    """좌석 예약 생성 검증 테스트"""

    def test_reserve_seat_with_specific_seat_id(self, db_session, test_user, test_seat):
        """특정 좌석 지정 예약 성공"""
        tomorrow = get_tomorrow()
        request = SeatReservationCreate(
            date=tomorrow,
            start_time=time(10, 0),
            end_time=time(12, 0),
            seat_id=test_seat.seat_id
        )

        reservation = seat_service.reserve_seat(db_session, test_user.student_id, request)

        assert reservation is not None
        assert reservation.seat_id == test_seat.seat_id
        assert reservation.student_id == test_user.student_id
        assert reservation.status == ReservationStatus.RESERVED

    def test_reserve_seat_random_assignment(self, db_session, test_user, available_seats):
        """랜덤 좌석 배정 예약 성공"""
        tomorrow = get_tomorrow()
        request = SeatReservationCreate(
            date=tomorrow,
            start_time=time(10, 0),
            end_time=time(12, 0),
            seat_id=None  # 랜덤 배정
        )

        reservation = seat_service.reserve_seat(db_session, test_user.student_id, request)

        assert reservation is not None
        assert reservation.seat_id is not None
        assert reservation.student_id == test_user.student_id

    def test_reserve_unavailable_seat_fails(self, db_session, test_user, reserved_seats):
        """이용 불가 좌석 예약 시도 → 에러"""
        unavailable_seat = reserved_seats[0]  # is_available=False
        tomorrow = get_tomorrow()

        request = SeatReservationCreate(
            date=tomorrow,
            start_time=time(10, 0),
            end_time=time(12, 0),
            seat_id=unavailable_seat.seat_id
        )

        with pytest.raises(BusinessException) as exc_info:
            seat_service.reserve_seat(db_session, test_user.student_id, request)

        assert exc_info.value.code == ErrorCode.SEAT_NOT_AVAILABLE


class TestSeatTimeConflict:
    """좌석 시간 충돌 검증 테스트

    NOTE: 다중 예약 시나리오는 서비스의 BEGIN IMMEDIATE 트랜잭션과 충돌하므로
    API 통합 테스트(test_seat_api.py)에서 테스트합니다.
    여기서는 기존 예약이 있는 상황에서의 충돌 검증을 fixture로 처리합니다.
    """

    def test_same_seat_same_time_conflict(self, db_session, test_user, test_seat, multiple_users, seat_reservation):
        """같은 좌석, 같은 시간대 예약 → 충돌 에러 (기존 예약 fixture 활용)"""
        # seat_reservation은 2025-12-20 12:00-14:00 (KST)에 test_seat을 예약
        other_user = multiple_users[0]

        # 같은 좌석, 같은 시간에 다른 사용자 예약 시도
        request = SeatReservationCreate(
            date=date(2025, 12, 20),
            start_time=time(12, 0),
            end_time=time(14, 0),
            seat_id=test_seat.seat_id
        )

        with pytest.raises(ConflictException) as exc_info:
            seat_service.reserve_seat(db_session, other_user.student_id, request)

        assert exc_info.value.code == ErrorCode.RESERVATION_CONFLICT

    def test_same_seat_different_time_no_conflict(self, db_session, test_seat, multiple_users, seat_reservation):
        """같은 좌석, 다른 시간대 예약 → 성공 (기존 예약 fixture 활용)"""
        # seat_reservation은 2025-12-20 12:00-14:00 (KST)에 test_seat을 예약
        other_user = multiple_users[0]

        # 같은 좌석, 다른 시간 (14:00-16:00)
        request = SeatReservationCreate(
            date=date(2025, 12, 20),
            start_time=time(14, 0),
            end_time=time(16, 0),
            seat_id=test_seat.seat_id
        )

        reservation = seat_service.reserve_seat(db_session, other_user.student_id, request)

        assert reservation is not None
        assert reservation.seat_id == test_seat.seat_id


class TestSeatOverlapWithOtherFacility:
    """다른 시설과의 중복 예약 검증 테스트

    NOTE: 다중 예약 시나리오(같은 시간대 다른 좌석)는 API 통합 테스트에서 검증합니다.
    """

    def test_cannot_reserve_seat_when_already_has_seat_reservation(self, db_session, test_user, available_seats, seat_reservation):
        """같은 시간대 좌석 예약이 이미 있으면 다른 좌석 예약 불가 (fixture 활용)"""
        # seat_reservation은 2025-12-20 12:00-14:00 (KST)에 test_seat 예약
        seat2 = available_seats[1]

        # 같은 시간대 다른 좌석 예약 시도
        request = SeatReservationCreate(
            date=date(2025, 12, 20),
            start_time=time(12, 0),
            end_time=time(14, 0),
            seat_id=seat2.seat_id
        )

        with pytest.raises(ConflictException) as exc_info:
            seat_service.reserve_seat(db_session, test_user.student_id, request)

        assert exc_info.value.code == ErrorCode.OVERLAP_WITH_OTHER_FACILITY

    def test_cannot_reserve_seat_when_has_meeting_room_reservation(self, db_session, test_user, test_seat, meeting_room_reservation):
        """같은 시간대 회의실 예약이 있으면 좌석 예약 불가"""
        # meeting_room_reservation은 2025-12-20 12:00-14:00 (KST)
        # 같은 시간대에 좌석 예약 시도
        request = SeatReservationCreate(
            date=date(2025, 12, 20),
            start_time=time(12, 0),
            end_time=time(14, 0),
            seat_id=test_seat.seat_id
        )

        with pytest.raises(ConflictException) as exc_info:
            seat_service.reserve_seat(db_session, test_user.student_id, request)

        assert exc_info.value.code == ErrorCode.OVERLAP_WITH_OTHER_FACILITY


class TestSeatDailyLimitValidation:
    """좌석 일일 한도 검증 테스트

    NOTE: 다중 예약 시나리오는 서비스의 BEGIN IMMEDIATE 트랜잭션과 충돌하므로
    API 통합 테스트(test_seat_api.py)에서 검증합니다.
    여기서는 기존 예약이 있는 상황(fixture)에서의 한도 검증을 테스트합니다.
    """

    def test_daily_limit_exceeded_with_existing_reservations(self, db_session, test_user, available_seats):
        """기존 예약으로 일일 한도에 도달한 경우 추가 예약 불가 (fixture로 기존 예약 시뮬레이션)"""
        # 직접 DB에 예약을 생성하여 240분 한도를 채움
        from app.models import Reservation, ReservationStatus
        from datetime import timezone as tz

        tomorrow = get_tomorrow()

        # 기존 예약 1: 10:00-12:00 (120분)
        reservation1 = Reservation(
            student_id=test_user.student_id,
            seat_id=available_seats[0].seat_id,
            meeting_room_id=None,
            start_time=datetime.combine(tomorrow, time(1, 0), tzinfo=tz.utc),  # KST 10:00
            end_time=datetime.combine(tomorrow, time(3, 0), tzinfo=tz.utc),    # KST 12:00
            status=ReservationStatus.RESERVED
        )
        db_session.add(reservation1)

        # 기존 예약 2: 14:00-16:00 (120분) → 총 240분
        reservation2 = Reservation(
            student_id=test_user.student_id,
            seat_id=available_seats[1].seat_id,
            meeting_room_id=None,
            start_time=datetime.combine(tomorrow, time(5, 0), tzinfo=tz.utc),  # KST 14:00
            end_time=datetime.combine(tomorrow, time(7, 0), tzinfo=tz.utc),    # KST 16:00
            status=ReservationStatus.RESERVED
        )
        db_session.add(reservation2)
        db_session.commit()

        # 추가 예약 시도 (16:00-18:00, 120분) → 총 360분, 한도 초과
        request = SeatReservationCreate(
            date=tomorrow,
            start_time=time(16, 0),
            end_time=time(18, 0),
            seat_id=available_seats[2].seat_id
        )

        with pytest.raises(LimitExceededException) as exc_info:
            seat_service.reserve_seat(db_session, test_user.student_id, request)

        assert exc_info.value.code == ErrorCode.DAILY_LIMIT_EXCEEDED

    def test_within_daily_limit_single_reservation(self, db_session, test_user, available_seats):
        """단일 예약은 일일 한도 내"""
        tomorrow = get_tomorrow()

        request = SeatReservationCreate(
            date=tomorrow,
            start_time=time(10, 0),
            end_time=time(12, 0),
            seat_id=available_seats[0].seat_id
        )
        reservation = seat_service.reserve_seat(db_session, test_user.student_id, request)

        assert reservation is not None
        assert reservation.seat_id == available_seats[0].seat_id


class TestRandomSeatAssignment:
    """랜덤 좌석 배정 로직 테스트

    NOTE: 다중 예약 시나리오는 API 통합 테스트에서 검증합니다.
    여기서는 기본적인 랜덤 배정 기능만 테스트합니다.
    """

    def test_random_assignment_when_seats_available(self, db_session, test_user, available_seats):
        """가용 좌석이 있을 때 랜덤 배정 성공"""
        tomorrow = get_tomorrow()
        request = SeatReservationCreate(
            date=tomorrow,
            start_time=time(10, 0),
            end_time=time(12, 0),
            seat_id=None
        )

        reservation = seat_service.reserve_seat(db_session, test_user.student_id, request)

        assert reservation is not None
        assert reservation.seat_id in [s.seat_id for s in available_seats]

    def test_random_assignment_avoids_occupied_seats(self, db_session, test_user, available_seats):
        """랜덤 배정 시 이미 예약된 좌석 제외 (fixture로 기존 예약 생성)"""
        from app.models import Reservation, ReservationStatus
        from datetime import timezone as tz

        tomorrow = get_tomorrow()

        # DB에 직접 예약을 생성하여 일부 좌석 점유
        for i in range(3):
            reservation = Reservation(
                student_id=202300000 + i,  # 임시 학번
                seat_id=available_seats[i].seat_id,
                meeting_room_id=None,
                start_time=datetime.combine(tomorrow, time(1, 0), tzinfo=tz.utc),  # KST 10:00
                end_time=datetime.combine(tomorrow, time(3, 0), tzinfo=tz.utc),    # KST 12:00
                status=ReservationStatus.RESERVED
            )
            db_session.add(reservation)
        db_session.commit()

        # 랜덤 배정 요청
        request = SeatReservationCreate(
            date=tomorrow,
            start_time=time(10, 0),
            end_time=time(12, 0),
            seat_id=None
        )

        reservation = seat_service.reserve_seat(db_session, test_user.student_id, request)

        # 예약된 좌석이 아닌 다른 좌석에 배정되어야 함
        occupied_seat_ids = [available_seats[i].seat_id for i in range(3)]
        assert reservation.seat_id not in occupied_seat_ids

    def test_random_assignment_fails_when_all_occupied(self, db_session, test_user, available_seats):
        """모든 좌석이 예약된 경우 랜덤 배정 실패 (fixture로 모든 좌석 점유)"""
        from app.models import Reservation, ReservationStatus
        from datetime import timezone as tz

        tomorrow = get_tomorrow()

        # DB에 직접 모든 좌석에 예약 생성
        for i, seat in enumerate(available_seats):
            reservation = Reservation(
                student_id=202300000 + i,  # 임시 학번
                seat_id=seat.seat_id,
                meeting_room_id=None,
                start_time=datetime.combine(tomorrow, time(1, 0), tzinfo=tz.utc),  # KST 10:00
                end_time=datetime.combine(tomorrow, time(3, 0), tzinfo=tz.utc),    # KST 12:00
                status=ReservationStatus.RESERVED
            )
            db_session.add(reservation)
        db_session.commit()

        # 랜덤 배정 요청 → 실패
        request = SeatReservationCreate(
            date=tomorrow,
            start_time=time(10, 0),
            end_time=time(12, 0),
            seat_id=None
        )

        with pytest.raises(ConflictException) as exc_info:
            seat_service.reserve_seat(db_session, test_user.student_id, request)

        assert exc_info.value.code == ErrorCode.RESERVATION_CONFLICT
