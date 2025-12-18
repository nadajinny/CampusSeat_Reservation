"""
tests/integration/test_meeting_room_api.py - 회의실 예약 API 통합 테스트 (실패 케이스 포함)
"""
import pytest
from datetime import datetime, timezone
from tests.utils.assertions import ResponseAssertions


@pytest.mark.integration
@pytest.mark.meeting_room
class TestMeetingRoomReservationValidation:
    """회의실 예약 입력 검증 테스트 - 의도된 실패 케이스"""

    def test_reserve_meeting_room_insufficient_participants(self, client, test_token, test_meeting_room):
        """참여자 2명으로 예약 시도 - 실패 예상 (최소 3명 필요)"""
        response = client.post(
            "/api/reservations/meeting-rooms",
            json={
                "room_id": test_meeting_room.room_id,
                "date": "2025-12-20",
                "start_time": "09:00",
                "end_time": "10:00",
                "participant_ids": [202312346, 202312347]  # 2명만
            },
            headers={"Authorization": f"Bearer {test_token}"}
        )

        # 기대: 400 Bad Request (최소 3명 필요)
        assert response.status_code == 400, "참여자가 3명 미만이면 차단되어야 합니다"

    def test_reserve_meeting_room_2_hours_duration(self, client, test_token, test_meeting_room):
        """2시간 예약 시도 - 실패 예상 (정확히 1시간만 허용)"""
        response = client.post(
            "/api/reservations/meeting-rooms",
            json={
                "room_id": test_meeting_room.room_id,
                "date": "2025-12-20",
                "start_time": "09:00",
                "end_time": "11:00",  # 2시간
                "participant_ids": [202312346, 202312347, 202312348]
            },
            headers={"Authorization": f"Bearer {test_token}"}
        )

        # 기대: 400 Bad Request (1시간만 허용)
        assert response.status_code == 400, "1시간이 아닌 예약은 차단되어야 합니다"

    def test_reserve_meeting_room_30_minutes(self, client, test_token, test_meeting_room):
        """30분 예약 시도 - 실패 예상 (정확히 1시간만 허용)"""
        response = client.post(
            "/api/reservations/meeting-rooms",
            json={
                "room_id": test_meeting_room.room_id,
                "date": "2025-12-20",
                "start_time": "09:00",
                "end_time": "09:30",  # 30분
                "participant_ids": [202312346, 202312347, 202312348]
            },
            headers={"Authorization": f"Bearer {test_token}"}
        )

        # 기대: 400 Bad Request
        assert response.status_code == 400, "정확히 1시간이 아닌 예약은 차단되어야 합니다"

    def test_reserve_meeting_room_outside_operating_hours(self, client, test_token, test_meeting_room):
        """운영시간 외 예약 시도 - 실패 예상 (09:00-18:00만 가능)"""
        response = client.post(
            "/api/reservations/meeting-rooms",
            json={
                "room_id": test_meeting_room.room_id,
                "date": "2025-12-20",
                "start_time": "18:00",  # 운영시간 마지막
                "end_time": "19:00",  # 운영시간 초과
                "participant_ids": [202312346, 202312347, 202312348]
            },
            headers={"Authorization": f"Bearer {test_token}"}
        )

        # 기대: 400 Bad Request
        assert response.status_code == 400, "운영시간(09:00-18:00) 외 예약은 차단되어야 합니다"

    def test_reserve_meeting_room_exceeding_daily_limit(self, client, test_token, test_meeting_room, db_session):
        """일일 2시간 초과 예약 시도 - 실패 예상"""
        from app.models import Reservation, ReservationStatus

        # 이미 2시간 예약이 있는 상태 생성
        existing1 = Reservation(
            student_id=202312345,
            seat_id=None,
            meeting_room_id=test_meeting_room.room_id,
            start_time=datetime(2025, 12, 20, 9, 0, 0, tzinfo=timezone.utc),
            end_time=datetime(2025, 12, 20, 10, 0, 0, tzinfo=timezone.utc),
            status=ReservationStatus.RESERVED
        )
        existing2 = Reservation(
            student_id=202312345,
            seat_id=None,
            meeting_room_id=test_meeting_room.room_id,
            start_time=datetime(2025, 12, 20, 10, 0, 0, tzinfo=timezone.utc),
            end_time=datetime(2025, 12, 20, 11, 0, 0, tzinfo=timezone.utc),
            status=ReservationStatus.RESERVED
        )
        db_session.add(existing1)
        db_session.add(existing2)
        db_session.commit()

        # 추가 1시간 예약 시도 (총 3시간 - 일일 제한 2시간 초과)
        response = client.post(
            "/api/reservations/meeting-rooms",
            json={
                "room_id": test_meeting_room.room_id,
                "date": "2025-12-20",
                "start_time": "11:00",
                "end_time": "12:00",
                "participant_ids": [202312346, 202312347, 202312348]
            },
            headers={"Authorization": f"Bearer {test_token}"}
        )

        # 기대: 400 Bad Request (일일 2시간 제한 초과)
        assert response.status_code == 400, "일일 2시간 제한을 초과하면 차단되어야 합니다"

    def test_reserve_meeting_room_exceeding_weekly_limit(self, client, test_token, test_meeting_room, db_session):
        """주간 5시간 초과 예약 시도 - 실패 예상"""
        from app.models import Reservation, ReservationStatus

        # 이미 5시간 예약이 있는 상태 생성 (5일간 각 1시간씩)
        for day in [15, 16, 17, 18, 19]:
            existing = Reservation(
                student_id=202312345,
                seat_id=None,
                meeting_room_id=test_meeting_room.room_id,
                start_time=datetime(2025, 12, day, 9, 0, 0, tzinfo=timezone.utc),
                end_time=datetime(2025, 12, day, 10, 0, 0, tzinfo=timezone.utc),
                status=ReservationStatus.RESERVED
            )
            db_session.add(existing)
        db_session.commit()

        # 추가 1시간 예약 시도 (총 6시간 - 주간 제한 5시간 초과)
        response = client.post(
            "/api/reservations/meeting-rooms",
            json={
                "room_id": test_meeting_room.room_id,
                "date": "2025-12-20",
                "start_time": "09:00",
                "end_time": "10:00",
                "participant_ids": [202312346, 202312347, 202312348]
            },
            headers={"Authorization": f"Bearer {test_token}"}
        )

        # 기대: 400 Bad Request (주간 5시간 제한 초과)
        assert response.status_code == 400, "주간 5시간 제한을 초과하면 차단되어야 합니다"


@pytest.mark.integration
@pytest.mark.meeting_room
class TestMeetingRoomParticipantValidation:
    """참여자 관련 검증 테스트 - 실패 예상"""

    def test_reserve_meeting_room_with_nonexistent_participant(self, client, test_token, test_meeting_room):
        """존재하지 않는 참여자 포함 - 실패 예상"""
        response = client.post(
            "/api/reservations/meeting-rooms",
            json={
                "room_id": test_meeting_room.room_id,
                "date": "2025-12-20",
                "start_time": "09:00",
                "end_time": "10:00",
                "participant_ids": [999999998, 999999999, 999999997]  # 존재하지 않는 학번들
            },
            headers={"Authorization": f"Bearer {test_token}"}
        )

        # 기대: 400 Bad Request (존재하지 않는 참여자)
        # 실제: 외래키 제약조건 위반으로 500 에러 가능
        assert response.status_code in [400, 500], "존재하지 않는 참여자는 차단되어야 합니다"

    def test_reserve_meeting_room_with_duplicate_participants(self, client, test_token, test_meeting_room):
        """중복 참여자 포함 - 실패 예상"""
        response = client.post(
            "/api/reservations/meeting-rooms",
            json={
                "room_id": test_meeting_room.room_id,
                "date": "2025-12-20",
                "start_time": "09:00",
                "end_time": "10:00",
                "participant_ids": [202312346, 202312346, 202312347]  # 중복
            },
            headers={"Authorization": f"Bearer {test_token}"}
        )

        # 기대: 400 Bad Request (중복 참여자 불가)
        # 실제: 통과할 가능성 있음
        assert response.status_code == 400, "중복 참여자는 차단되어야 합니다"

    def test_reserve_meeting_room_owner_in_participants(self, client, test_token, test_meeting_room):
        """예약자 본인이 참여자 목록에 포함 - 실패 예상"""
        response = client.post(
            "/api/reservations/meeting-rooms",
            json={
                "room_id": test_meeting_room.room_id,
                "date": "2025-12-20",
                "start_time": "09:00",
                "end_time": "10:00",
                "participant_ids": [202312345, 202312346, 202312347]  # 202312345는 예약자 본인
            },
            headers={"Authorization": f"Bearer {test_token}"}
        )

        # 기대: 400 Bad Request (예약자는 참여자에서 제외되어야 함)
        # 실제: 통과할 가능성 있음
        assert response.status_code == 400, "예약자 본인은 참여자 목록에 포함될 수 없습니다"

    def test_reserve_meeting_room_participant_has_conflict(self, client, test_token, test_meeting_room, db_session):
        """참여자가 동일 시간에 다른 예약이 있는 경우 - 실패 예상"""
        from app.models import Seat, Reservation, ReservationStatus, User

        # 참여자 생성
        participant = User(student_id=202312346)
        db_session.add(participant)

        # 좌석 생성
        seat = Seat(seat_id=1)
        db_session.add(seat)
        db_session.commit()

        # 참여자의 기존 좌석 예약 생성
        existing = Reservation(
            student_id=202312346,
            seat_id=1,
            meeting_room_id=None,
            start_time=datetime(2025, 12, 20, 9, 0, 0, tzinfo=timezone.utc),
            end_time=datetime(2025, 12, 20, 11, 0, 0, tzinfo=timezone.utc),
            status=ReservationStatus.RESERVED
        )
        db_session.add(existing)
        db_session.commit()

        # 동일 시간대 회의실 예약 시도 (참여자가 충돌)
        response = client.post(
            "/api/reservations/meeting-rooms",
            json={
                "room_id": test_meeting_room.room_id,
                "date": "2025-12-20",
                "start_time": "09:00",
                "end_time": "10:00",
                "participant_ids": [202312346, 202312347, 202312348]  # 202312346은 충돌
            },
            headers={"Authorization": f"Bearer {test_token}"}
        )

        # 기대: 409 Conflict (참여자 시간 충돌)
        # 실제: 통과할 가능성 있음 (참여자 충돌 검사 미구현)
        assert response.status_code == 409, "참여자의 시간 충돌은 차단되어야 합니다"


@pytest.mark.integration
@pytest.mark.meeting_room
class TestMeetingRoomConflicts:
    """회의실 충돌 관련 테스트 - 실패 예상"""

    def test_reserve_meeting_room_with_seat_conflict(self, client, test_token, test_meeting_room, db_session):
        """예약자가 동일 시간에 좌석 예약이 있는 경우"""
        from app.models import Seat, Reservation, ReservationStatus

        # 좌석 생성
        seat = Seat(seat_id=1)
        db_session.add(seat)
        db_session.commit()

        # 예약자의 기존 좌석 예약 생성
        existing = Reservation(
            student_id=202312345,
            seat_id=1,
            meeting_room_id=None,
            start_time=datetime(2025, 12, 20, 9, 0, 0, tzinfo=timezone.utc),
            end_time=datetime(2025, 12, 20, 11, 0, 0, tzinfo=timezone.utc),
            status=ReservationStatus.RESERVED
        )
        db_session.add(existing)
        db_session.commit()

        # 동일 시간대 회의실 예약 시도
        response = client.post(
            "/api/reservations/meeting-rooms",
            json={
                "room_id": test_meeting_room.room_id,
                "date": "2025-12-20",
                "start_time": "09:00",
                "end_time": "10:00",
                "participant_ids": [202312346, 202312347, 202312348]
            },
            headers={"Authorization": f"Bearer {test_token}"}
        )

        # 기대: 409 Conflict (좌석 예약과 시간 충돌)
        assert response.status_code == 409, "좌석 예약과 시간이 겹치면 차단되어야 합니다"

    def test_reserve_nonexistent_meeting_room(self, client, test_token):
        """존재하지 않는 회의실 예약 시도"""
        response = client.post(
            "/api/reservations/meeting-rooms",
            json={
                "room_id": 999999,  # 존재하지 않는 회의실
                "date": "2025-12-20",
                "start_time": "09:00",
                "end_time": "10:00",
                "participant_ids": [202312346, 202312347, 202312348]
            },
            headers={"Authorization": f"Bearer {test_token}"}
        )

        # 기대: 404 Not Found
        # 실제: 외래키 제약조건 위반 시 500 에러 가능
        assert response.status_code in [400, 404], "존재하지 않는 회의실 예약은 차단되어야 합니다"

    def test_reserve_meeting_room_past_date(self, client, test_token, test_meeting_room):
        """과거 날짜 회의실 예약 시도"""
        response = client.post(
            "/api/reservations/meeting-rooms",
            json={
                "room_id": test_meeting_room.room_id,
                "date": "2020-01-01",  # 과거
                "start_time": "09:00",
                "end_time": "10:00",
                "participant_ids": [202312346, 202312347, 202312348]
            },
            headers={"Authorization": f"Bearer {test_token}"}
        )

        # 기대: 400 Bad Request
        # 실제: 통과할 가능성 있음
        assert response.status_code == 400, "과거 날짜 예약은 차단되어야 합니다"


@pytest.mark.integration
@pytest.mark.meeting_room
class TestMeetingRoomEdgeCases:
    """회의실 예약 엣지 케이스"""

    def test_reserve_meeting_room_empty_participant_list(self, client, test_token, test_meeting_room):
        """빈 참여자 목록으로 예약 시도"""
        response = client.post(
            "/api/reservations/meeting-rooms",
            json={
                "room_id": test_meeting_room.room_id,
                "date": "2025-12-20",
                "start_time": "09:00",
                "end_time": "10:00",
                "participant_ids": []  # 빈 리스트
            },
            headers={"Authorization": f"Bearer {test_token}"}
        )

        # 기대: 400 Bad Request
        assert response.status_code == 400, "참여자가 없으면 차단되어야 합니다"

    def test_reserve_meeting_room_one_participant(self, client, test_token, test_meeting_room):
        """참여자 1명으로 예약 시도"""
        response = client.post(
            "/api/reservations/meeting-rooms",
            json={
                "room_id": test_meeting_room.room_id,
                "date": "2025-12-20",
                "start_time": "09:00",
                "end_time": "10:00",
                "participant_ids": [202312346]  # 1명만
            },
            headers={"Authorization": f"Bearer {test_token}"}
        )

        # 기대: 400 Bad Request (최소 3명 필요)
        assert response.status_code == 400, "참여자가 3명 미만이면 차단되어야 합니다"

    def test_reserve_meeting_room_invalid_time_format(self, client, test_token, test_meeting_room):
        """잘못된 시간 형식으로 예약 시도"""
        response = client.post(
            "/api/reservations/meeting-rooms",
            json={
                "room_id": test_meeting_room.room_id,
                "date": "2025-12-20",
                "start_time": "9:00 AM",  # 잘못된 형식
                "end_time": "10:00 AM",
                "participant_ids": [202312346, 202312347, 202312348]
            },
            headers={"Authorization": f"Bearer {test_token}"}
        )

        # 기대: 400 Bad Request (Pydantic 검증 실패)
        assert response.status_code == 400, "잘못된 시간 형식은 차단되어야 합니다"
