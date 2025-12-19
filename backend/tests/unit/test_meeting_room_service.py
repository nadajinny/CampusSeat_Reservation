"""
tests/unit/test_meeting_room_service.py - 회의실 예약 서비스 단위 테스트
"""
import pytest
from datetime import datetime, date, time, timedelta, timezone

from app.services import meeting_room_service
from app.schemas.meeting_room import MeetingRoomReservationCreate, ParticipantBase
from app.models import ReservationStatus, Reservation, MeetingRoom
from app.constants import ErrorCode, ReservationLimits
from app.exceptions import ConflictException, LimitExceededException, ValidationException


KST = timezone(timedelta(hours=9))
UTC = timezone.utc


def get_tomorrow():
    return date.today() + timedelta(days=1)


def create_participants(student_ids):
    """참여자 리스트 생성 헬퍼"""
    return [ParticipantBase(student_id=sid) for sid in student_ids]


class TestMeetingRoomQuery:
    """회의실 조회 로직 테스트"""

    def test_get_meeting_room_count(self, db_session, available_meeting_rooms):
        """회의실 총 개수 조회"""
        count = meeting_room_service.get_meeting_room_count(db_session)

        assert count >= len(available_meeting_rooms)


class TestMeetingRoomReservationCreation:
    """회의실 예약 생성 검증 테스트"""

    def test_reserve_meeting_room_success(self, db_session, test_user, test_meeting_room, multiple_users):
        """회의실 예약 성공"""
        tomorrow = get_tomorrow()
        participants = create_participants([u.student_id for u in multiple_users[:3]])

        request = MeetingRoomReservationCreate(
            room_id=test_meeting_room.room_id,
            date=tomorrow,
            start_time=time(10, 0),
            end_time=time(11, 0),
            participants=participants
        )

        reservation = meeting_room_service.process_reservation(
            db_session, test_user.student_id, request
        )

        assert reservation is not None
        assert reservation.meeting_room_id == test_meeting_room.room_id
        assert reservation.student_id == test_user.student_id
        assert reservation.status == ReservationStatus.RESERVED

    def test_reserve_invalid_room_id_fails(self, db_session, test_user, multiple_users):
        """유효하지 않은 회의실 ID → 스키마 검증 에러"""
        from pydantic import ValidationError

        tomorrow = get_tomorrow()
        participants = create_participants([u.student_id for u in multiple_users[:3]])

        # room_id=99는 허용된 ID(1, 2, 3)가 아니므로 스키마 검증에서 실패
        with pytest.raises(ValidationError):
            MeetingRoomReservationCreate(
                room_id=99,
                date=tomorrow,
                start_time=time(10, 0),
                end_time=time(11, 0),
                participants=participants
            )


class TestParticipantValidation:
    """참여자 검증 로직 테스트"""

    def test_min_participants_required(self, db_session, test_user, test_meeting_room):
        """최소 참여자(3명) 미달 → 에러"""
        tomorrow = get_tomorrow()
        # 2명만 참여 (최소 3명 필요)
        participants = create_participants([202312346, 202312347])

        # pydantic validation에서 에러 발생
        with pytest.raises(ValueError):
            MeetingRoomReservationCreate(
                room_id=test_meeting_room.room_id,
                date=tomorrow,
                start_time=time(10, 0),
                end_time=time(11, 0),
                participants=participants
            )

    def test_duplicate_participants_rejected(self, db_session, test_user, test_meeting_room):
        """중복 참여자 → 에러"""
        tomorrow = get_tomorrow()
        # 중복된 학번
        participants = create_participants([202312346, 202312346, 202312347])

        with pytest.raises(ValueError):
            MeetingRoomReservationCreate(
                room_id=test_meeting_room.room_id,
                date=tomorrow,
                start_time=time(10, 0),
                end_time=time(11, 0),
                participants=participants
            )


class TestMeetingRoomConflictValidation:
    """회의실 예약 충돌 검증 테스트"""

    def test_same_room_same_time_conflict(self, db_session, test_user, test_meeting_room, multiple_users):
        """같은 회의실, 같은 시간대 예약 → 충돌 에러"""
        tomorrow = get_tomorrow()
        participants1 = create_participants([u.student_id for u in multiple_users[:3]])

        # 첫 번째 예약
        request1 = MeetingRoomReservationCreate(
            room_id=test_meeting_room.room_id,
            date=tomorrow,
            start_time=time(10, 0),
            end_time=time(11, 0),
            participants=participants1
        )
        meeting_room_service.process_reservation(db_session, test_user.student_id, request1)

        # 다른 사용자가 같은 회의실, 같은 시간에 예약 시도
        other_user = multiple_users[4]
        participants2 = create_participants([202399901, 202399902, 202399903])

        request2 = MeetingRoomReservationCreate(
            room_id=test_meeting_room.room_id,
            date=tomorrow,
            start_time=time(10, 0),
            end_time=time(11, 0),
            participants=participants2
        )

        with pytest.raises(ConflictException) as exc_info:
            meeting_room_service.process_reservation(db_session, other_user.student_id, request2)

        assert exc_info.value.code == ErrorCode.RESERVATION_CONFLICT

    def test_same_room_different_time_no_conflict(self, db_session, test_user, test_meeting_room, multiple_users):
        """같은 회의실, 다른 시간대 → 성공"""
        tomorrow = get_tomorrow()
        participants1 = create_participants([u.student_id for u in multiple_users[:3]])

        # 첫 번째 예약 (10:00-11:00)
        request1 = MeetingRoomReservationCreate(
            room_id=test_meeting_room.room_id,
            date=tomorrow,
            start_time=time(10, 0),
            end_time=time(11, 0),
            participants=participants1
        )
        meeting_room_service.process_reservation(db_session, test_user.student_id, request1)

        # 같은 회의실, 다른 시간 (14:00-15:00)
        other_user = multiple_users[4]
        participants2 = create_participants([202399901, 202399902, 202399903])

        request2 = MeetingRoomReservationCreate(
            room_id=test_meeting_room.room_id,
            date=tomorrow,
            start_time=time(14, 0),
            end_time=time(15, 0),
            participants=participants2
        )

        reservation2 = meeting_room_service.process_reservation(
            db_session, other_user.student_id, request2
        )

        assert reservation2 is not None


class TestParticipantOverlapValidation:
    """참여자 중복 예약 검증 테스트"""

    def test_participant_already_has_reservation_conflict(self, db_session, test_user, available_meeting_rooms, multiple_users):
        """참여자가 같은 시간대 다른 예약에 있으면 에러"""
        tomorrow = get_tomorrow()
        room1 = available_meeting_rooms[0]
        room2 = available_meeting_rooms[1]

        # 참여자 A, B, C로 첫 번째 예약
        participants1 = create_participants([u.student_id for u in multiple_users[:3]])
        request1 = MeetingRoomReservationCreate(
            room_id=room1.room_id,
            date=tomorrow,
            start_time=time(10, 0),
            end_time=time(11, 0),
            participants=participants1
        )
        meeting_room_service.process_reservation(db_session, test_user.student_id, request1)

        # 참여자 A가 포함된 두 번째 예약 시도 (같은 시간)
        other_user = multiple_users[4]
        overlapping_participant = multiple_users[0].student_id  # 첫 번째 예약 참여자
        participants2 = create_participants([overlapping_participant, 202399902, 202399903])

        request2 = MeetingRoomReservationCreate(
            room_id=room2.room_id,
            date=tomorrow,
            start_time=time(10, 0),
            end_time=time(11, 0),
            participants=participants2
        )

        with pytest.raises(ConflictException) as exc_info:
            meeting_room_service.process_reservation(db_session, other_user.student_id, request2)

        assert exc_info.value.code == ErrorCode.OVERLAP_WITH_OTHER_FACILITY


class TestMeetingRoomDailyLimitValidation:
    """회의실 일일 한도 검증 테스트"""

    def test_daily_limit_exceeded(self, db_session, test_user, available_meeting_rooms, multiple_users):
        """일일 한도(120분) 초과 시 에러"""
        tomorrow = get_tomorrow()

        # 첫 번째 예약 (10:00-11:00, 60분)
        participants1 = create_participants([u.student_id for u in multiple_users[:3]])
        request1 = MeetingRoomReservationCreate(
            room_id=available_meeting_rooms[0].room_id,
            date=tomorrow,
            start_time=time(10, 0),
            end_time=time(11, 0),
            participants=participants1
        )
        meeting_room_service.process_reservation(db_session, test_user.student_id, request1)

        # 두 번째 예약 (14:00-15:00, 60분) → 총 120분
        participants2 = create_participants([202399901, 202399902, 202399903])
        request2 = MeetingRoomReservationCreate(
            room_id=available_meeting_rooms[1].room_id,
            date=tomorrow,
            start_time=time(14, 0),
            end_time=time(15, 0),
            participants=participants2
        )
        meeting_room_service.process_reservation(db_session, test_user.student_id, request2)

        # 세 번째 예약 시도 (16:00-17:00, 60분) → 총 180분, 한도 초과
        participants3 = create_participants([202399904, 202399905, 202399906])
        request3 = MeetingRoomReservationCreate(
            room_id=available_meeting_rooms[2].room_id,
            date=tomorrow,
            start_time=time(16, 0),
            end_time=time(17, 0),
            participants=participants3
        )

        with pytest.raises(LimitExceededException) as exc_info:
            meeting_room_service.process_reservation(db_session, test_user.student_id, request3)

        assert exc_info.value.code == ErrorCode.DAILY_LIMIT_EXCEEDED

    def test_within_daily_limit(self, db_session, test_user, available_meeting_rooms, multiple_users):
        """일일 한도 내 예약 성공"""
        tomorrow = get_tomorrow()

        # 첫 번째 예약 (10:00-11:00, 60분)
        participants1 = create_participants([u.student_id for u in multiple_users[:3]])
        request1 = MeetingRoomReservationCreate(
            room_id=available_meeting_rooms[0].room_id,
            date=tomorrow,
            start_time=time(10, 0),
            end_time=time(11, 0),
            participants=participants1
        )
        reservation1 = meeting_room_service.process_reservation(
            db_session, test_user.student_id, request1
        )

        # 두 번째 예약 (14:00-15:00, 60분) → 총 120분, 한도 내
        participants2 = create_participants([202399901, 202399902, 202399903])
        request2 = MeetingRoomReservationCreate(
            room_id=available_meeting_rooms[1].room_id,
            date=tomorrow,
            start_time=time(14, 0),
            end_time=time(15, 0),
            participants=participants2
        )
        reservation2 = meeting_room_service.process_reservation(
            db_session, test_user.student_id, request2
        )

        assert reservation1 is not None
        assert reservation2 is not None


def get_next_monday():
    """다음 주 월요일 반환"""
    today = date.today()
    days_until_monday = (7 - today.weekday()) % 7
    if days_until_monday == 0:
        days_until_monday = 7  # 오늘이 월요일이면 다음 주 월요일
    return today + timedelta(days=days_until_monday)


def get_same_week_dates(count):
    """다음 주 월~토 날짜들을 반환 (같은 주 보장)"""
    monday = get_next_monday()
    return [monday + timedelta(days=i) for i in range(count)]


class TestMeetingRoomWeeklyLimitValidation:
    """회의실 주간 한도 검증 테스트

    NOTE: 주간 한도는 월요일부터 일요일까지 기준입니다.
    여기서는 기존 예약이 있는 상황(fixture)에서의 주간 한도 검증을 테스트합니다.
    """

    def test_weekly_limit_exceeded(self, db_session, test_user, available_meeting_rooms, multiple_users):
        """주간 한도(300분) 초과 시 에러 - fixture로 기존 예약 생성"""
        from datetime import timezone as tz

        # 다음 주 월~토 날짜들 (같은 주 보장)
        week_dates = get_same_week_dates(6)

        # DB에 직접 5일 동안의 예약 생성 (총 300분)
        for i in range(5):
            target_date = week_dates[i]
            reservation = Reservation(
                student_id=test_user.student_id,
                meeting_room_id=available_meeting_rooms[i % len(available_meeting_rooms)].room_id,
                seat_id=None,
                start_time=datetime.combine(target_date, time(1, 0), tzinfo=tz.utc),  # KST 10:00
                end_time=datetime.combine(target_date, time(2, 0), tzinfo=tz.utc),    # KST 11:00
                status=ReservationStatus.RESERVED
            )
            db_session.add(reservation)
        db_session.commit()

        # 6번째 예약 시도 (같은 주 토요일) → 주간 한도 초과
        sixth_date = week_dates[5]  # 토요일
        participants6 = create_participants([u.student_id for u in multiple_users[:3]])

        request6 = MeetingRoomReservationCreate(
            room_id=available_meeting_rooms[0].room_id,
            date=sixth_date,
            start_time=time(14, 0),  # 다른 시간대
            end_time=time(15, 0),
            participants=participants6
        )

        with pytest.raises(LimitExceededException) as exc_info:
            meeting_room_service.process_reservation(db_session, test_user.student_id, request6)

        assert exc_info.value.code == ErrorCode.WEEKLY_LIMIT_EXCEEDED

    def test_participant_weekly_limit_exceeded(self, db_session, test_user, available_meeting_rooms, multiple_users):
        """참여자의 주간 한도 초과 시 에러 - fixture로 기존 예약 생성"""
        from datetime import timezone as tz
        from app.models import ReservationParticipant

        # 다음 주 월~토 날짜들 (같은 주 보장)
        week_dates = get_same_week_dates(6)
        participant_user = multiple_users[0]

        # DB에 직접 5일 동안의 예약 및 참여자 생성 (총 300분)
        for i in range(5):
            target_date = week_dates[i]
            reservation = Reservation(
                student_id=test_user.student_id,
                meeting_room_id=available_meeting_rooms[i % len(available_meeting_rooms)].room_id,
                seat_id=None,
                start_time=datetime.combine(target_date, time(5, 0), tzinfo=tz.utc),  # KST 14:00
                end_time=datetime.combine(target_date, time(6, 0), tzinfo=tz.utc),    # KST 15:00
                status=ReservationStatus.RESERVED
            )
            db_session.add(reservation)
            db_session.flush()

            # participant_user를 참여자로 추가 (participant_student_id 필드 사용)
            participant = ReservationParticipant(
                reservation_id=reservation.reservation_id,
                participant_student_id=participant_user.student_id
            )
            db_session.add(participant)
        db_session.commit()

        # 6번째 예약에 participant_user가 다시 참여 (같은 주 토요일) → 주간 한도 초과
        sixth_date = week_dates[5]  # 토요일
        participants6 = create_participants([
            participant_user.student_id,
            multiple_users[4].student_id,
            multiple_users[5].student_id
        ])

        request6 = MeetingRoomReservationCreate(
            room_id=available_meeting_rooms[0].room_id,
            date=sixth_date,
            start_time=time(16, 0),
            end_time=time(17, 0),
            participants=participants6
        )

        with pytest.raises(LimitExceededException) as exc_info:
            # 다른 신청자가 예약하지만, participant_user가 참여자로 있음
            other_applicant = multiple_users[4]
            meeting_room_service.process_reservation(db_session, other_applicant.student_id, request6)

        assert exc_info.value.code == ErrorCode.WEEKLY_LIMIT_EXCEEDED


class TestMeetingRoomOverlapWithSeat:
    """좌석 예약과의 중복 검증 테스트"""

    def test_cannot_reserve_meeting_room_when_has_seat_reservation(self, db_session, test_user, test_meeting_room, seat_reservation, multiple_users):
        """좌석 예약이 있는 시간대에 회의실 예약 불가"""
        # seat_reservation은 2025-12-20 11:00-13:00 (KST)
        participants = create_participants([u.student_id for u in multiple_users[:3]])

        request = MeetingRoomReservationCreate(
            room_id=test_meeting_room.room_id,
            date=date(2025, 12, 20),
            start_time=time(12, 0),  # 좌석 예약과 겹침
            end_time=time(13, 0),
            participants=participants
        )

        with pytest.raises(ConflictException) as exc_info:
            meeting_room_service.process_reservation(
                db_session, test_user.student_id, request
            )

        assert exc_info.value.code == ErrorCode.OVERLAP_WITH_OTHER_FACILITY
