"""
tests/integration/test_meeting_room_api.py - 회의실 예약 API 통합 테스트
"""
import pytest
from datetime import date, timedelta
from tests.utils.assertions import ResponseAssertions, ReservationAssertions


def get_tomorrow():
    return (date.today() + timedelta(days=1)).isoformat()


def get_next_week_dates():
    """다음 주 날짜들 반환 (주간 한도 테스트용)"""
    tomorrow = date.today() + timedelta(days=1)
    return [(tomorrow + timedelta(days=i)).isoformat() for i in range(7)]


def get_auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def make_participants(users):
    """사용자 목록을 participants 형식으로 변환"""
    return [{"student_id": u.student_id} for u in users]


@pytest.mark.integration
@pytest.mark.meeting_room
class TestCreateMeetingRoomReservationAPI:
    """회의실 예약 생성 API 테스트"""

    def test_create_meeting_room_reservation_success(self, client, test_token, test_meeting_room, multiple_users):
        """회의실 예약 생성 성공 - 201 Created"""
        tomorrow = get_tomorrow()
        participants = make_participants(multiple_users[:3])

        response = client.post(
            "/api/reservations/meeting-rooms",
            headers=get_auth_headers(test_token),
            json={
                "date": tomorrow,
                "start_time": "10:00",
                "end_time": "11:00",
                "room_id": test_meeting_room.room_id,
                "participants": participants
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["is_success"] is True
        assert data["payload"]["meeting_room_id"] == test_meeting_room.room_id
        assert data["payload"]["status"] == "RESERVED"

    def test_create_meeting_room_reservation_response_format(self, client, test_token, test_meeting_room, multiple_users):
        """예약 생성 응답 형식 검증"""
        tomorrow = get_tomorrow()
        participants = make_participants(multiple_users[:3])

        response = client.post(
            "/api/reservations/meeting-rooms",
            headers=get_auth_headers(test_token),
            json={
                "date": tomorrow,
                "start_time": "10:00",
                "end_time": "11:00",
                "room_id": test_meeting_room.room_id,
                "participants": participants
            }
        )

        data = response.json()
        payload = data["payload"]
        assert "reservation_id" in payload
        assert "meeting_room_id" in payload
        assert "start_time" in payload
        assert "end_time" in payload
        assert "status" in payload

    def test_create_meeting_room_reservation_without_auth(self, client, test_meeting_room, multiple_users):
        """인증 없이 예약 시도 - 400 Bad Request"""
        tomorrow = get_tomorrow()
        participants = make_participants(multiple_users[:3])

        response = client.post(
            "/api/reservations/meeting-rooms",
            json={
                "date": tomorrow,
                "start_time": "10:00",
                "end_time": "11:00",
                "room_id": test_meeting_room.room_id,
                "participants": participants
            }
        )

        assert response.status_code == 400


@pytest.mark.integration
@pytest.mark.meeting_room
class TestMeetingRoomParticipantValidationAPI:
    """회의실 참가자 검증 API 테스트"""

    def test_minimum_participants_required(self, client, test_token, test_meeting_room, multiple_users):
        """최소 참가자 수(3명) 미만 → 400 에러"""
        tomorrow = get_tomorrow()
        # 2명만 참가자로 지정
        participants = make_participants(multiple_users[:2])

        response = client.post(
            "/api/reservations/meeting-rooms",
            headers=get_auth_headers(test_token),
            json={
                "date": tomorrow,
                "start_time": "10:00",
                "end_time": "11:00",
                "room_id": test_meeting_room.room_id,
                "participants": participants
            }
        )

        assert response.status_code == 400
        data = response.json()
        assert data["is_success"] is False
        assert data["code"] == "VALIDATION_ERROR"

    def test_three_participants_success(self, client, test_token, test_meeting_room, multiple_users):
        """정확히 3명 참가자 → 성공"""
        tomorrow = get_tomorrow()
        participants = make_participants(multiple_users[:3])

        response = client.post(
            "/api/reservations/meeting-rooms",
            headers=get_auth_headers(test_token),
            json={
                "date": tomorrow,
                "start_time": "10:00",
                "end_time": "11:00",
                "room_id": test_meeting_room.room_id,
                "participants": participants
            }
        )

        assert response.status_code == 201


@pytest.mark.integration
@pytest.mark.meeting_room
class TestMeetingRoomTimeConflictAPI:
    """회의실 시간 충돌 API 테스트"""

    def test_same_room_same_time_conflict(self, client, test_token, test_meeting_room, multiple_users):
        """같은 회의실, 같은 시간 예약 → 409 Conflict"""
        tomorrow = get_tomorrow()
        participants = make_participants(multiple_users[:3])

        # 첫 번째 예약
        response1 = client.post(
            "/api/reservations/meeting-rooms",
            headers=get_auth_headers(test_token),
            json={
                "date": tomorrow,
                "start_time": "10:00",
                "end_time": "11:00",
                "room_id": test_meeting_room.room_id,
                "participants": participants
            }
        )
        assert response1.status_code == 201

        # 다른 사용자 토큰 생성
        from uuid import uuid4
        other_token = f"token-{multiple_users[3].student_id}-{uuid4().hex}"
        other_participants = make_participants(multiple_users[3:6])

        # 같은 회의실, 같은 시간 예약 시도
        response2 = client.post(
            "/api/reservations/meeting-rooms",
            headers=get_auth_headers(other_token),
            json={
                "date": tomorrow,
                "start_time": "10:00",
                "end_time": "11:00",
                "room_id": test_meeting_room.room_id,
                "participants": other_participants
            }
        )

        assert response2.status_code == 409
        data = response2.json()
        assert data["is_success"] is False
        assert data["code"] == "RESERVATION_CONFLICT"

    def test_same_room_different_time_success(self, client, test_token, test_meeting_room, multiple_users):
        """같은 회의실, 다른 시간 예약 → 성공"""
        tomorrow = get_tomorrow()
        participants = make_participants(multiple_users[:3])

        # 첫 번째 예약
        response1 = client.post(
            "/api/reservations/meeting-rooms",
            headers=get_auth_headers(test_token),
            json={
                "date": tomorrow,
                "start_time": "10:00",
                "end_time": "11:00",
                "room_id": test_meeting_room.room_id,
                "participants": participants
            }
        )
        assert response1.status_code == 201

        # 다른 사용자 토큰
        from uuid import uuid4
        other_token = f"token-{multiple_users[3].student_id}-{uuid4().hex}"
        other_participants = make_participants(multiple_users[3:6])

        # 같은 회의실, 다른 시간
        response2 = client.post(
            "/api/reservations/meeting-rooms",
            headers=get_auth_headers(other_token),
            json={
                "date": tomorrow,
                "start_time": "14:00",
                "end_time": "15:00",
                "room_id": test_meeting_room.room_id,
                "participants": other_participants
            }
        )

        assert response2.status_code == 201


@pytest.mark.integration
@pytest.mark.meeting_room
class TestMeetingRoomDailyLimitAPI:
    """회의실 일일 한도 API 테스트"""

    def test_daily_limit_exceeded(self, client, test_token, available_meeting_rooms, multiple_users):
        """일일 한도(120분) 초과 시 400 에러"""
        tomorrow = get_tomorrow()
        participants = make_participants(multiple_users[:3])

        # 첫 번째 예약 (60분)
        response1 = client.post(
            "/api/reservations/meeting-rooms",
            headers=get_auth_headers(test_token),
            json={
                "date": tomorrow,
                "start_time": "10:00",
                "end_time": "11:00",
                "room_id": available_meeting_rooms[0].room_id,
                "participants": participants
            }
        )
        assert response1.status_code == 201

        # 두 번째 예약 (60분) → 총 120분, 아직 한도 내
        response2 = client.post(
            "/api/reservations/meeting-rooms",
            headers=get_auth_headers(test_token),
            json={
                "date": tomorrow,
                "start_time": "14:00",
                "end_time": "15:00",
                "room_id": available_meeting_rooms[1].room_id,
                "participants": participants
            }
        )
        assert response2.status_code == 201

        # 세 번째 예약 시도 (60분) → 총 180분, 한도 초과
        response3 = client.post(
            "/api/reservations/meeting-rooms",
            headers=get_auth_headers(test_token),
            json={
                "date": tomorrow,
                "start_time": "16:00",
                "end_time": "17:00",
                "room_id": available_meeting_rooms[2].room_id,
                "participants": participants
            }
        )

        assert response3.status_code == 400
        data = response3.json()
        assert data["is_success"] is False
        assert data["code"] == "DAILY_LIMIT_EXCEEDED"


@pytest.mark.integration
@pytest.mark.meeting_room
class TestMeetingRoomWeeklyLimitAPI:
    """회의실 주간 한도 API 테스트

    NOTE: 주간 한도 테스트는 날짜 경계 계산이 복잡하여 단위 테스트에서
    DB fixture로 검증합니다. 여기서는 기본 예약 기능만 확인합니다.
    """

    def test_multiple_reservations_in_week(self, client, test_token, available_meeting_rooms, multiple_users):
        """같은 주 내 여러 예약 생성 가능 확인"""
        dates = get_next_week_dates()
        participants = make_participants(multiple_users[:3])

        # 첫 번째 예약
        response1 = client.post(
            "/api/reservations/meeting-rooms",
            headers=get_auth_headers(test_token),
            json={
                "date": dates[0],
                "start_time": "10:00",
                "end_time": "11:00",
                "room_id": available_meeting_rooms[0].room_id,
                "participants": participants
            }
        )
        assert response1.status_code == 201

        # 두 번째 예약 (다른 날짜, 다른 시간)
        response2 = client.post(
            "/api/reservations/meeting-rooms",
            headers=get_auth_headers(test_token),
            json={
                "date": dates[1],
                "start_time": "14:00",
                "end_time": "15:00",
                "room_id": available_meeting_rooms[1].room_id,
                "participants": participants
            }
        )
        assert response2.status_code == 201


@pytest.mark.integration
@pytest.mark.meeting_room
class TestMeetingRoomParticipantOverlapAPI:
    """회의실 참가자 중복 예약 API 테스트"""

    def test_participant_already_has_reservation(self, client, test_token, available_meeting_rooms, multiple_users):
        """참가자가 이미 같은 시간대 예약이 있으면 에러"""
        tomorrow = get_tomorrow()
        participants = make_participants(multiple_users[:3])

        # 첫 번째 예약
        response1 = client.post(
            "/api/reservations/meeting-rooms",
            headers=get_auth_headers(test_token),
            json={
                "date": tomorrow,
                "start_time": "10:00",
                "end_time": "11:00",
                "room_id": available_meeting_rooms[0].room_id,
                "participants": participants
            }
        )
        assert response1.status_code == 201

        # 다른 사용자가 같은 참가자 포함하여 예약 시도
        from uuid import uuid4
        other_token = f"token-{multiple_users[4].student_id}-{uuid4().hex}"
        # participants[0] (multiple_users[0])이 이미 예약에 포함됨
        overlapping_participants = [
            {"student_id": multiple_users[0].student_id},
            {"student_id": multiple_users[4].student_id},
            {"student_id": multiple_users[5].student_id}
        ]

        response2 = client.post(
            "/api/reservations/meeting-rooms",
            headers=get_auth_headers(other_token),
            json={
                "date": tomorrow,
                "start_time": "10:00",
                "end_time": "11:00",
                "room_id": available_meeting_rooms[1].room_id,
                "participants": overlapping_participants
            }
        )

        assert response2.status_code == 409
        data = response2.json()
        assert data["is_success"] is False
        # 참가자 중복은 OVERLAP_WITH_OTHER_FACILITY로 처리됨
        assert data["code"] in ["PARTICIPANT_ALREADY_RESERVED", "OVERLAP_WITH_OTHER_FACILITY"]


@pytest.mark.integration
@pytest.mark.meeting_room
class TestMeetingRoomOverlapWithSeatAPI:
    """회의실과 좌석 간 중복 예약 API 테스트"""

    def test_cannot_reserve_meeting_room_when_has_seat_reservation(self, client, test_token, test_meeting_room, test_seat, multiple_users):
        """같은 시간대 좌석 예약이 있으면 회의실 예약 불가"""
        tomorrow = get_tomorrow()

        # 먼저 좌석 예약
        response1 = client.post(
            "/api/reservations/seats",
            headers=get_auth_headers(test_token),
            json={
                "date": tomorrow,
                "start_time": "10:00",
                "end_time": "12:00",
                "seat_id": test_seat.seat_id
            }
        )
        assert response1.status_code == 201

        # 같은 시간대 회의실 예약 시도
        participants = make_participants(multiple_users[:3])
        response2 = client.post(
            "/api/reservations/meeting-rooms",
            headers=get_auth_headers(test_token),
            json={
                "date": tomorrow,
                "start_time": "10:00",
                "end_time": "11:00",
                "room_id": test_meeting_room.room_id,
                "participants": participants
            }
        )

        assert response2.status_code == 409
        data = response2.json()
        assert data["is_success"] is False
        assert data["code"] == "OVERLAP_WITH_OTHER_FACILITY"


@pytest.mark.integration
@pytest.mark.meeting_room
class TestMeetingRoomValidationAPI:
    """회의실 예약 입력값 검증 API 테스트"""

    def test_invalid_time_range(self, client, test_token, test_meeting_room, multiple_users):
        """종료 시간이 시작 시간보다 빠름 → 400 에러"""
        tomorrow = get_tomorrow()
        participants = make_participants(multiple_users[:3])

        response = client.post(
            "/api/reservations/meeting-rooms",
            headers=get_auth_headers(test_token),
            json={
                "date": tomorrow,
                "start_time": "14:00",
                "end_time": "12:00",  # 잘못된 시간
                "room_id": test_meeting_room.room_id,
                "participants": participants
            }
        )

        assert response.status_code == 400

    def test_not_1hour_duration(self, client, test_token, test_meeting_room, multiple_users):
        """1시간 단위가 아닌 예약 → 400 에러"""
        tomorrow = get_tomorrow()
        participants = make_participants(multiple_users[:3])

        response = client.post(
            "/api/reservations/meeting-rooms",
            headers=get_auth_headers(test_token),
            json={
                "date": tomorrow,
                "start_time": "10:00",
                "end_time": "10:30",  # 30분만
                "room_id": test_meeting_room.room_id,
                "participants": participants
            }
        )

        assert response.status_code == 400

    def test_outside_operation_hours(self, client, test_token, test_meeting_room, multiple_users):
        """운영 시간 외 예약 → 400 에러"""
        tomorrow = get_tomorrow()
        participants = make_participants(multiple_users[:3])

        response = client.post(
            "/api/reservations/meeting-rooms",
            headers=get_auth_headers(test_token),
            json={
                "date": tomorrow,
                "start_time": "07:00",  # 운영 시간 전
                "end_time": "08:00",
                "room_id": test_meeting_room.room_id,
                "participants": participants
            }
        )

        assert response.status_code == 400

    def test_past_date_reservation(self, client, test_token, test_meeting_room, multiple_users):
        """과거 날짜 예약 → 400 에러"""
        past_date = (date.today() - timedelta(days=1)).isoformat()
        participants = make_participants(multiple_users[:3])

        response = client.post(
            "/api/reservations/meeting-rooms",
            headers=get_auth_headers(test_token),
            json={
                "date": past_date,
                "start_time": "10:00",
                "end_time": "11:00",
                "room_id": test_meeting_room.room_id,
                "participants": participants
            }
        )

        assert response.status_code == 400


@pytest.mark.integration
@pytest.mark.meeting_room
class TestMeetingRoomStatusAPI:
    """회의실 상태 조회 API 테스트 (status 엔드포인트 활용)"""

    def test_get_meeting_room_status(self, client, available_meeting_rooms):
        """회의실 현황 조회"""
        tomorrow = get_tomorrow()
        response = client.get(f"/api/status/meeting-rooms?date={tomorrow}")

        assert response.status_code == 200
        data = response.json()
        assert data["is_success"] is True
        assert "rooms" in data["payload"]
        assert len(data["payload"]["rooms"]) >= len(available_meeting_rooms)
