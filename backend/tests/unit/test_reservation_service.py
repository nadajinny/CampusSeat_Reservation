"""
tests/unit/test_reservation_service.py - 예약 서비스 단위 테스트
"""
import pytest
from datetime import datetime, date, time

from app.services import reservation_service
from app.models import ReservationStatus
from app.constants import ErrorCode
from app.exceptions import BusinessException, ForbiddenException


class TestReservationQuery:
    """예약 조회 로직 테스트"""

    def test_get_user_reservations(self, db_session, test_user, seat_reservation):
        """사용자의 모든 예약 조회"""
        # 실행
        reservations = reservation_service.get_user_reservations(db_session, test_user.student_id)

        # 검증
        assert len(reservations) >= 1
        assert any(r.reservation_id == seat_reservation.reservation_id for r in reservations)

    def test_get_user_reservations_filtered_by_date(self, db_session, test_user, seat_reservation):
        """날짜 필터링된 예약 조회"""
        # 실행
        reservations = reservation_service.get_user_reservations(db_session, test_user.student_id)

        # 특정 날짜의 예약만 필터링
        target_date = date(2025, 12, 20)
        filtered = [r for r in reservations if r.start_time.date() == target_date]

        # 검증
        assert len(filtered) >= 1
        for reservation in filtered:
            assert reservation.start_time.date() == target_date

    def test_get_user_reservations_filtered_by_type(self, db_session, test_user, seat_reservation, meeting_room_reservation):
        """타입 필터링된 예약 조회 (meeting_room/seat)"""
        # 실행
        reservations = reservation_service.get_user_reservations(db_session, test_user.student_id)

        # 좌석 예약만 필터링
        seat_reservations = [r for r in reservations if r.seat_id is not None]
        meeting_reservations = [r for r in reservations if r.meeting_room_id is not None]

        # 검증
        assert len(seat_reservations) >= 1
        assert len(meeting_reservations) >= 1
        assert all(r.seat_id is not None for r in seat_reservations)
        assert all(r.meeting_room_id is not None for r in meeting_reservations)

    def test_get_empty_reservations(self, db_session):
        """예약이 없는 사용자"""
        # 존재하지 않는 사용자 ID
        non_existent_user_id = 999999999

        # 실행
        reservations = reservation_service.get_user_reservations(db_session, non_existent_user_id)

        # 검증
        assert len(reservations) == 0


class TestReservationCancellation:
    """예약 취소 검증 테스트"""

    def test_cancel_reserved_reservation(self, db_session, test_user, seat_reservation):
        """RESERVED 상태의 예약 취소 성공"""
        # 실행
        result = reservation_service.cancel_reservation(
            db_session,
            seat_reservation.reservation_id,
            test_user.student_id
        )

        # 검증
        assert result.status == ReservationStatus.CANCELED
        assert result.reservation_id == seat_reservation.reservation_id

    def test_cancel_already_canceled_reservation(self, db_session, test_user, canceled_reservation):
        """이미 취소된 예약 중복 취소 시도 → 400 에러"""
        # 실행 및 검증
        with pytest.raises(BusinessException) as exc_info:
            reservation_service.cancel_reservation(
                db_session,
                canceled_reservation.reservation_id,
                test_user.student_id
            )

        assert exc_info.value.code == ErrorCode.RESERVATION_ALREADY_CANCELED

    def test_cancel_in_use_reservation(self, db_session, test_user, test_seat):
        """IN_USE 상태의 예약 취소 시도 → 403 에러"""
        # IN_USE 상태의 예약 생성
        from app.models import Reservation
        from datetime import timezone

        in_use_reservation = Reservation(
            student_id=test_user.student_id,
            seat_id=test_seat.seat_id,
            meeting_room_id=None,
            start_time=datetime(2025, 12, 20, 2, 0, 0, tzinfo=timezone.utc),
            end_time=datetime(2025, 12, 20, 4, 0, 0, tzinfo=timezone.utc),
            status=ReservationStatus.IN_USE
        )
        db_session.add(in_use_reservation)
        db_session.commit()
        db_session.refresh(in_use_reservation)

        # 실행 및 검증
        with pytest.raises(ForbiddenException) as exc_info:
            reservation_service.cancel_reservation(
                db_session,
                in_use_reservation.reservation_id,
                test_user.student_id
            )

        assert exc_info.value.code == ErrorCode.AUTH_FORBIDDEN

    def test_cancel_completed_reservation(self, db_session, test_user, expired_reservation):
        """COMPLETED 상태의 예약 취소 시도 → 403 에러"""
        # 실행 및 검증
        with pytest.raises(ForbiddenException) as exc_info:
            reservation_service.cancel_reservation(
                db_session,
                expired_reservation.reservation_id,
                test_user.student_id
            )

        assert exc_info.value.code == ErrorCode.AUTH_FORBIDDEN

    def test_cancel_other_user_reservation(self, db_session, test_user, seat_reservation, multiple_users):
        """다른 사용자의 예약 취소 시도 → 403 에러"""
        other_user = multiple_users[0]

        # 실행 및 검증
        with pytest.raises(ForbiddenException) as exc_info:
            reservation_service.cancel_reservation(
                db_session,
                seat_reservation.reservation_id,
                other_user.student_id
            )

        assert exc_info.value.code == ErrorCode.AUTH_FORBIDDEN

    def test_cancel_nonexistent_reservation(self, db_session, test_user):
        """존재하지 않는 예약 취소 시도 → 404 에러"""
        non_existent_id = 999999

        # 실행 및 검증
        with pytest.raises(BusinessException) as exc_info:
            reservation_service.cancel_reservation(
                db_session,
                non_existent_id,
                test_user.student_id
            )

        assert exc_info.value.code == ErrorCode.NOT_FOUND


class TestReservationCancellationResponse:
    """예약 취소 응답 검증 테스트"""

    def test_cancel_response_contains_type(self, db_session, test_user, seat_reservation):
        """취소 응답에 type 필드 포함"""
        # 실행
        result = reservation_service.cancel_reservation(
            db_session,
            seat_reservation.reservation_id,
            test_user.student_id
        )

        # 검증 - 좌석 타입 확인
        assert result.seat_id is not None or result.meeting_room_id is not None

    def test_cancel_response_contains_facility_info(self, db_session, test_user, seat_reservation):
        """취소 응답에 room_id/seat_id 포함"""
        # 실행
        result = reservation_service.cancel_reservation(
            db_session,
            seat_reservation.reservation_id,
            test_user.student_id
        )

        # 검증
        assert result.seat_id == seat_reservation.seat_id
        assert result.meeting_room_id is None

    def test_cancel_meeting_room_response(self, db_session, test_user, meeting_room_reservation):
        """회의실 예약 취소 응답 형식"""
        # 실행
        result = reservation_service.cancel_reservation(
            db_session,
            meeting_room_reservation.reservation_id,
            test_user.student_id
        )

        # 검증
        assert result.meeting_room_id == meeting_room_reservation.meeting_room_id
        assert result.seat_id is None
        assert result.status == ReservationStatus.CANCELED

    def test_cancel_seat_response(self, db_session, test_user, seat_reservation):
        """좌석 예약 취소 응답 형식"""
        # 실행
        result = reservation_service.cancel_reservation(
            db_session,
            seat_reservation.reservation_id,
            test_user.student_id
        )

        # 검증
        assert result.seat_id == seat_reservation.seat_id
        assert result.meeting_room_id is None
        assert result.status == ReservationStatus.CANCELED


class TestReservationConflictDetection:
    """예약 충돌 감지 로직 테스트"""

    def test_detect_same_facility_conflict(self, db_session, test_user, seat_reservation):
        """같은 시설 동일 시간대 충돌 감지"""
        # 같은 시간대, 같은 좌석에 예약 시도
        has_overlap = reservation_service.check_overlap_with_other_facility(
            db_session,
            test_user.student_id,
            seat_reservation.start_time,
            seat_reservation.end_time,
            include_seats=True,
            include_meeting_rooms=False
        )

        # 검증
        assert has_overlap is True

    def test_detect_no_conflict_different_time(self, db_session, test_user, seat_reservation):
        """다른 시간대는 충돌 없음"""
        from datetime import timezone

        # 다른 시간대 (기존 예약 이후)
        new_start = datetime(2025, 12, 20, 5, 0, 0, tzinfo=timezone.utc)
        new_end = datetime(2025, 12, 20, 7, 0, 0, tzinfo=timezone.utc)

        has_overlap = reservation_service.check_overlap_with_other_facility(
            db_session,
            test_user.student_id,
            new_start,
            new_end,
            include_seats=True,
            include_meeting_rooms=False
        )

        # 검증
        assert has_overlap is False

    def test_detect_no_conflict_different_facility(self, db_session, test_user, seat_reservation):
        """다른 시설은 충돌 없음"""
        # 같은 시간대이지만 회의실만 체크 (좌석 예약은 있지만 회의실은 없음)
        has_overlap = reservation_service.check_overlap_with_other_facility(
            db_session,
            test_user.student_id,
            seat_reservation.start_time,
            seat_reservation.end_time,
            include_seats=False,
            include_meeting_rooms=True
        )

        # 검증
        assert has_overlap is False


class TestReservationStateTransition:
    """예약 상태 전이 로직 테스트"""

    def test_reserved_to_in_use(self, db_session, test_user, seat_reservation):
        """RESERVED → IN_USE 전이"""
        # 상태 변경
        seat_reservation.status = ReservationStatus.IN_USE
        db_session.commit()
        db_session.refresh(seat_reservation)

        # 검증
        assert seat_reservation.status == ReservationStatus.IN_USE

    def test_in_use_to_completed(self, db_session, test_user, test_seat):
        """IN_USE → COMPLETED 전이"""
        from app.models import Reservation
        from datetime import timezone

        # IN_USE 예약 생성
        reservation = Reservation(
            student_id=test_user.student_id,
            seat_id=test_seat.seat_id,
            meeting_room_id=None,
            start_time=datetime(2025, 12, 20, 2, 0, 0, tzinfo=timezone.utc),
            end_time=datetime(2025, 12, 20, 4, 0, 0, tzinfo=timezone.utc),
            status=ReservationStatus.IN_USE
        )
        db_session.add(reservation)
        db_session.commit()

        # 상태 변경
        reservation.status = ReservationStatus.COMPLETED
        db_session.commit()
        db_session.refresh(reservation)

        # 검증
        assert reservation.status == ReservationStatus.COMPLETED

    def test_reserved_to_canceled(self, db_session, test_user, seat_reservation):
        """RESERVED → CANCELED 전이"""
        # 실행
        result = reservation_service.cancel_reservation(
            db_session,
            seat_reservation.reservation_id,
            test_user.student_id
        )

        # 검증
        assert result.status == ReservationStatus.CANCELED


class TestFacilityOverlapValidation:
    """시설 중복 예약 검증 테스트"""

    def test_cannot_reserve_seat_when_meeting_room_reserved(self, db_session, test_user, meeting_room_reservation):
        """회의실 예약 중 좌석 예약 시도 → 에러"""
        # 회의실 예약과 같은 시간대에 좌석 예약 충돌 체크
        has_overlap = reservation_service.check_overlap_with_other_facility(
            db_session,
            test_user.student_id,
            meeting_room_reservation.start_time,
            meeting_room_reservation.end_time,
            include_seats=False,
            include_meeting_rooms=True
        )

        # 검증
        assert has_overlap is True

    def test_cannot_reserve_meeting_room_when_seat_reserved(self, db_session, test_user, seat_reservation):
        """좌석 예약 중 회의실 예약 시도 → 에러"""
        # 좌석 예약과 같은 시간대에 회의실 예약 충돌 체크
        has_overlap = reservation_service.check_overlap_with_other_facility(
            db_session,
            test_user.student_id,
            seat_reservation.start_time,
            seat_reservation.end_time,
            include_seats=True,
            include_meeting_rooms=False
        )

        # 검증
        assert has_overlap is True

    def test_can_reserve_different_time_slots(self, db_session, test_user, seat_reservation):
        """다른 시간대는 둘 다 예약 가능"""
        from datetime import timezone

        # 다른 시간대
        new_start = datetime(2025, 12, 20, 5, 0, 0, tzinfo=timezone.utc)
        new_end = datetime(2025, 12, 20, 7, 0, 0, tzinfo=timezone.utc)

        # 좌석 체크
        seat_overlap = reservation_service.check_overlap_with_other_facility(
            db_session,
            test_user.student_id,
            new_start,
            new_end,
            include_seats=True,
            include_meeting_rooms=False
        )

        # 회의실 체크
        room_overlap = reservation_service.check_overlap_with_other_facility(
            db_session,
            test_user.student_id,
            new_start,
            new_end,
            include_seats=False,
            include_meeting_rooms=True
        )

        # 검증
        assert seat_overlap is False
        assert room_overlap is False
