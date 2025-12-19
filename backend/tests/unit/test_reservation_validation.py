"""
tests/unit/test_reservation_validation.py - 예약 검증 로직 단위 테스트 (실패 케이스 포함)
"""
import pytest
from datetime import datetime, time, date, timezone
from app.services.reservation_service import check_overlap_with_other_facility


@pytest.mark.unit
class TestReservationTimeValidation:
    """예약 시간 검증 로직 테스트 - 실패 예상"""

    def test_validate_future_date_only(self):
        """과거 날짜 검증 - 실패 예상 (구현되지 않았을 수 있음)"""
        from datetime import date, timedelta

        past_date = date.today() - timedelta(days=1)
        future_date = date.today() + timedelta(days=1)

        # 실제 구현에서는 이 검증이 없을 수 있음
        # 이 테스트는 실패할 것으로 예상됨
        # 가정: validate_reservation_date 함수가 존재한다면
        try:
            from app.services.validation import validate_reservation_date

            with pytest.raises(Exception):
                validate_reservation_date(past_date)

            # 미래 날짜는 통과
            validate_reservation_date(future_date)
        except ImportError:
            # 함수가 없으면 테스트 실패
            pytest.fail("validate_reservation_date 함수가 구현되지 않았습니다")

    def test_validate_2_hour_intervals_only(self):
        """2시간 단위 검증 - 실패 예상"""
        # 가정: 2시간 단위만 허용하는 검증 함수가 있다면
        try:
            from app.services.validation import validate_time_interval

            # 2시간 단위가 아닌 경우 실패해야 함
            with pytest.raises(Exception):
                validate_time_interval(time(9, 0), time(10, 30))  # 1.5시간

            with pytest.raises(Exception):
                validate_time_interval(time(9, 0), time(12, 0))  # 3시간

            # 2시간 단위는 통과
            validate_time_interval(time(9, 0), time(11, 0))
        except ImportError:
            pytest.fail("validate_time_interval 함수가 구현되지 않았습니다")

    def test_validate_operating_hours(self):
        """운영 시간 검증 - 실패 예상"""
        try:
            from app.services.validation import validate_operating_hours

            # 운영시간 외
            with pytest.raises(Exception):
                validate_operating_hours(time(8, 0), time(10, 0))  # 08:00 시작

            with pytest.raises(Exception):
                validate_operating_hours(time(20, 0), time(22, 0))  # 22:00 종료

            # 운영시간 내
            validate_operating_hours(time(9, 0), time(11, 0))
        except ImportError:
            pytest.fail("validate_operating_hours 함수가 구현되지 않았습니다")


@pytest.mark.unit
class TestSeatReservationLimits:
    """좌석 예약 제한 검증 - 실패 예상"""

    def test_daily_limit_calculation_edge_case(self, db_session, test_user, test_seat):
        """일일 제한 계산 엣지 케이스 - 정확히 4시간"""
        from app.models import Reservation, ReservationStatus

        # 정확히 4시간 예약
        reservation = Reservation(
            student_id=test_user.student_id,
            seat_id=test_seat.seat_id,
            meeting_room_id=None,
            start_time=datetime(2025, 12, 20, 9, 0, 0, tzinfo=timezone.utc),
            end_time=datetime(2025, 12, 20, 13, 0, 0, tzinfo=timezone.utc),
            status=ReservationStatus.RESERVED
        )
        db_session.add(reservation)
        db_session.commit()

        # 추가 예약 시도 (실패해야 함)
        try:
            from app.services.validation import check_daily_seat_limit

            with pytest.raises(Exception):
                check_daily_seat_limit(
                    db_session,
                    test_user.student_id,
                    date(2025, 12, 20),
                    2  # 추가 2시간
                )
        except ImportError:
            pytest.fail("check_daily_seat_limit 함수가 구현되지 않았습니다")

    def test_daily_limit_with_canceled_reservations(self, db_session, test_user, test_seat):
        """취소된 예약은 제한에 포함되지 않아야 함 - 실패 예상"""
        from app.models import Reservation, ReservationStatus

        # 취소된 예약 4시간
        canceled = Reservation(
            student_id=test_user.student_id,
            seat_id=test_seat.seat_id,
            meeting_room_id=None,
            start_time=datetime(2025, 12, 20, 9, 0, 0, tzinfo=timezone.utc),
            end_time=datetime(2025, 12, 20, 13, 0, 0, tzinfo=timezone.utc),
            status=ReservationStatus.CANCELED
        )
        db_session.add(canceled)
        db_session.commit()

        # 추가 4시간 예약 시도 (성공해야 함 - 취소된 예약은 제한에 포함 안 됨)
        try:
            from app.services.validation import check_daily_seat_limit

            # 취소된 예약은 제한에 포함되지 않으므로 통과해야 함
            check_daily_seat_limit(
                db_session,
                test_user.student_id,
                date(2025, 12, 20),
                4  # 4시간
            )
        except Exception as e:
            pytest.fail(f"취소된 예약은 제한에 포함되지 않아야 하는데 실패: {e}")


@pytest.mark.unit
class TestMeetingRoomReservationLimits:
    """회의실 예약 제한 검증 - 실패 예상"""

    def test_weekly_limit_calculation_across_weeks(self, db_session, test_user, test_meeting_room):
        """주간 제한 계산 - 주가 바뀔 때 엣지 케이스"""
        from app.models import Reservation, ReservationStatus

        # 이전 주 예약 (제한에 포함되지 않아야 함)
        prev_week = Reservation(
            student_id=test_user.student_id,
            seat_id=None,
            meeting_room_id=test_meeting_room.room_id,
            start_time=datetime(2025, 12, 13, 9, 0, 0, tzinfo=timezone.utc),  # 토요일
            end_time=datetime(2025, 12, 13, 14, 0, 0, tzinfo=timezone.utc),  # 5시간
            status=ReservationStatus.RESERVED
        )
        db_session.add(prev_week)
        db_session.commit()

        # 새로운 주(월요일) 예약 시도 (통과해야 함)
        try:
            from app.services.validation import check_weekly_meeting_room_limit

            # 이전 주 예약은 제한에 포함 안 되므로 통과해야 함
            check_weekly_meeting_room_limit(
                db_session,
                test_user.student_id,
                date(2025, 12, 15),  # 다음 주 월요일
                5  # 5시간
            )
        except Exception as e:
            pytest.fail(f"이전 주 예약은 제한에 포함되지 않아야 하는데 실패: {e}")

    def test_daily_and_weekly_limit_interaction(self, db_session, test_user, test_meeting_room):
        """일일 제한과 주간 제한 상호작용 - 실패 예상"""
        from app.models import Reservation, ReservationStatus

        # 5일간 각 2시간씩 예약 (주간 한도 10시간 사용, 하지만 일일 한도는 2시간)
        for day in [15, 16, 17, 18, 19]:
            res1 = Reservation(
                student_id=test_user.student_id,
                seat_id=None,
                meeting_room_id=test_meeting_room.room_id,
                start_time=datetime(2025, 12, day, 9, 0, 0, tzinfo=timezone.utc),
                end_time=datetime(2025, 12, day, 10, 0, 0, tzinfo=timezone.utc),
                status=ReservationStatus.RESERVED
            )
            res2 = Reservation(
                student_id=test_user.student_id,
                seat_id=None,
                meeting_room_id=test_meeting_room.room_id,
                start_time=datetime(2025, 12, day, 10, 0, 0, tzinfo=timezone.utc),
                end_time=datetime(2025, 12, day, 11, 0, 0, tzinfo=timezone.utc),
                status=ReservationStatus.RESERVED
            )
            db_session.add(res1)
            db_session.add(res2)
        db_session.commit()

        # 추가 예약 시도 (주간 한도 초과)
        try:
            from app.services.validation import check_weekly_meeting_room_limit

            with pytest.raises(Exception):
                check_weekly_meeting_room_limit(
                    db_session,
                    test_user.student_id,
                    date(2025, 12, 20),
                    1  # 추가 1시간
                )
        except ImportError:
            pytest.fail("check_weekly_meeting_room_limit 함수가 구현되지 않았습니다")


@pytest.mark.unit
class TestOverlapDetection:
    """시간 겹침 검사 로직 테스트"""

    def test_overlap_detection_boundary_case_same_end_start(self, db_session, test_user):
        """경계 케이스: 종료 시간 = 시작 시간 (겹치지 않아야 함)"""
        from app.models import Seat, Reservation, ReservationStatus

        seat = Seat(seat_id=1)
        db_session.add(seat)
        db_session.commit()

        # 기존 예약: 09:00-11:00
        existing = Reservation(
            student_id=test_user.student_id,
            seat_id=1,
            meeting_room_id=None,
            start_time=datetime(2025, 12, 20, 9, 0, 0, tzinfo=timezone.utc),
            end_time=datetime(2025, 12, 20, 11, 0, 0, tzinfo=timezone.utc),
            status=ReservationStatus.RESERVED
        )
        db_session.add(existing)
        db_session.commit()

        # 새 예약: 11:00-13:00 (경계가 정확히 맞음)
        has_overlap = check_overlap_with_other_facility(
            db_session,
            test_user.student_id,
            datetime(2025, 12, 20, 11, 0, 0, tzinfo=timezone.utc),
            datetime(2025, 12, 20, 13, 0, 0, tzinfo=timezone.utc)
        )

        # 경계가 정확히 맞으면 겹치지 않아야 함
        assert not has_overlap, "종료시간=시작시간인 경우 겹치지 않아야 합니다"

    def test_overlap_detection_one_minute_overlap(self, db_session, test_user):
        """1분이라도 겹치면 충돌로 감지해야 함"""
        from app.models import Seat, Reservation, ReservationStatus

        seat = Seat(seat_id=1)
        db_session.add(seat)
        db_session.commit()

        # 기존 예약: 09:00-11:00
        existing = Reservation(
            student_id=test_user.student_id,
            seat_id=1,
            meeting_room_id=None,
            start_time=datetime(2025, 12, 20, 9, 0, 0, tzinfo=timezone.utc),
            end_time=datetime(2025, 12, 20, 11, 0, 0, tzinfo=timezone.utc),
            status=ReservationStatus.RESERVED
        )
        db_session.add(existing)
        db_session.commit()

        # 새 예약: 10:59-12:59 (1분 겹침)
        has_overlap = check_overlap_with_other_facility(
            db_session,
            test_user.student_id,
            datetime(2025, 12, 20, 10, 59, 0, tzinfo=timezone.utc),
            datetime(2025, 12, 20, 12, 59, 0, tzinfo=timezone.utc)
        )

        # 1분이라도 겹치면 충돌
        assert has_overlap, "1분이라도 겹치면 충돌로 감지되어야 합니다"


@pytest.mark.unit
class TestParticipantValidation:
    """참여자 검증 로직 - 실패 예상"""

    def test_validate_participant_count_boundary(self):
        """참여자 수 경계값 검증"""
        try:
            from app.services.validation import validate_participant_count

            # 2명 - 실패
            with pytest.raises(Exception):
                validate_participant_count([1, 2])

            # 3명 - 성공
            validate_participant_count([1, 2, 3])

            # 빈 리스트 - 실패
            with pytest.raises(Exception):
                validate_participant_count([])
        except ImportError:
            pytest.fail("validate_participant_count 함수가 구현되지 않았습니다")

    def test_validate_no_duplicate_participants(self):
        """중복 참여자 검증"""
        try:
            from app.services.validation import validate_no_duplicate_participants

            # 중복 있음 - 실패
            with pytest.raises(Exception):
                validate_no_duplicate_participants([1, 2, 2, 3])

            # 중복 없음 - 성공
            validate_no_duplicate_participants([1, 2, 3])
        except ImportError:
            pytest.fail("validate_no_duplicate_participants 함수가 구현되지 않았습니다")

    def test_validate_owner_not_in_participants(self):
        """예약자는 참여자 목록에 없어야 함"""
        try:
            from app.services.validation import validate_owner_not_in_participants

            owner_id = 202312345

            # 예약자가 참여자에 포함 - 실패
            with pytest.raises(Exception):
                validate_owner_not_in_participants(owner_id, [202312345, 202312346, 202312347])

            # 예약자가 참여자에 없음 - 성공
            validate_owner_not_in_participants(owner_id, [202312346, 202312347, 202312348])
        except ImportError:
            pytest.fail("validate_owner_not_in_participants 함수가 구현되지 않았습니다")


@pytest.mark.unit
class TestStatusTransitionValidation:
    """예약 상태 전이 검증 - 실패 예상"""

    def test_cannot_cancel_completed_reservation(self):
        """COMPLETED 상태는 취소 불가"""
        try:
            from app.models import ReservationStatus
            from app.services.validation import can_cancel_reservation

            # COMPLETED 상태 - 취소 불가
            assert not can_cancel_reservation(ReservationStatus.COMPLETED)

            # RESERVED 상태 - 취소 가능
            assert can_cancel_reservation(ReservationStatus.RESERVED)

            # CANCELED 상태 - 취소 불가
            assert not can_cancel_reservation(ReservationStatus.CANCELED)

            # IN_USE 상태 - 취소 불가
            assert not can_cancel_reservation(ReservationStatus.IN_USE)
        except ImportError:
            pytest.fail("can_cancel_reservation 함수가 구현되지 않았습니다")

    def test_status_transition_validation(self):
        """예약 상태 전이 규칙 검증"""
        try:
            from app.models import ReservationStatus
            from app.services.validation import is_valid_status_transition

            # RESERVED → IN_USE (가능)
            assert is_valid_status_transition(ReservationStatus.RESERVED, ReservationStatus.IN_USE)

            # RESERVED → CANCELED (가능)
            assert is_valid_status_transition(ReservationStatus.RESERVED, ReservationStatus.CANCELED)

            # CANCELED → RESERVED (불가능)
            assert not is_valid_status_transition(ReservationStatus.CANCELED, ReservationStatus.RESERVED)

            # COMPLETED → IN_USE (불가능)
            assert not is_valid_status_transition(ReservationStatus.COMPLETED, ReservationStatus.IN_USE)
        except ImportError:
            pytest.fail("is_valid_status_transition 함수가 구현되지 않았습니다")
