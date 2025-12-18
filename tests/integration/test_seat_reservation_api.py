"""
tests/integration/test_seat_reservation_api.py - 좌석 예약 API 통합 테스트 (실패 케이스 포함)
"""
import pytest
from datetime import datetime, time
from tests.utils.assertions import ResponseAssertions


@pytest.mark.integration
@pytest.mark.seat_reservation
class TestSeatReservationValidation:
    """좌석 예약 입력 검증 테스트 - 의도된 실패 케이스"""

    def test_reserve_seat_past_date(self, client, test_token, test_seat):
        """과거 날짜로 예약 시도 - 실패 예상 (구현되지 않은 검증)"""
        # 이 테스트는 실패할 것으로 예상됨: 과거 날짜 검증이 구현되지 않았을 수 있음
        response = client.post(
            "/api/reservations/seats",
            json={
                "seat_id": test_seat.seat_id,
                "date": "2020-01-01",  # 과거 날짜
                "start_time": "09:00",
                "end_time": "11:00"
            },
            headers={"Authorization": f"Bearer {test_token}"}
        )

        # 기대: 400 Bad Request (과거 날짜 불가)
        # 실제: 200 OK로 통과할 가능성이 있음
        assert response.status_code == 400, "과거 날짜 예약이 차단되어야 합니다"

    def test_reserve_seat_invalid_time_unit(self, client, test_token, test_seat):
        """30분 단위 시간으로 예약 시도 - 실패 예상 (2시간 단위만 허용)"""
        # 이 테스트는 실패할 것으로 예상됨: 30분 단위는 허용되지 않아야 함
        response = client.post(
            "/api/reservations/seats",
            json={
                "seat_id": test_seat.seat_id,
                "date": "2025-12-20",
                "start_time": "09:30",  # 30분 단위
                "end_time": "11:30"
            },
            headers={"Authorization": f"Bearer {test_token}"}
        )

        # 기대: 400 Bad Request (2시간 단위만 허용)
        # 실제: 통과할 가능성 있음
        assert response.status_code == 400, "2시간 단위가 아닌 예약은 차단되어야 합니다"

    def test_reserve_seat_3_hours_duration(self, client, test_token, test_seat):
        """3시간 예약 시도 - 실패 예상 (2시간 단위만 허용)"""
        # 이 테스트는 실패할 것으로 예상됨: 3시간은 2시간 단위가 아님
        response = client.post(
            "/api/reservations/seats",
            json={
                "seat_id": test_seat.seat_id,
                "date": "2025-12-20",
                "start_time": "09:00",
                "end_time": "12:00"  # 3시간
            },
            headers={"Authorization": f"Bearer {test_token}"}
        )

        # 기대: 400 Bad Request
        # 실제: 통과할 가능성 있음
        assert response.status_code == 400, "2시간 단위가 아닌 예약은 차단되어야 합니다"

    def test_reserve_seat_outside_operating_hours_early(self, client, test_token, test_seat):
        """운영시간 이전 예약 시도 - 실패 예상"""
        # 운영시간: 09:00-21:00
        response = client.post(
            "/api/reservations/seats",
            json={
                "seat_id": test_seat.seat_id,
                "date": "2025-12-20",
                "start_time": "07:00",  # 운영시간 전
                "end_time": "09:00"
            },
            headers={"Authorization": f"Bearer {test_token}"}
        )

        # 기대: 400 Bad Request
        assert response.status_code == 400, "운영시간 외 예약은 차단되어야 합니다"

    def test_reserve_seat_outside_operating_hours_late(self, client, test_token, test_seat):
        """운영시간 이후 예약 시도 - 실패 예상"""
        response = client.post(
            "/api/reservations/seats",
            json={
                "seat_id": test_seat.seat_id,
                "date": "2025-12-20",
                "start_time": "21:00",  # 운영시간 마지막
                "end_time": "23:00"  # 운영시간 초과
            },
            headers={"Authorization": f"Bearer {test_token}"}
        )

        # 기대: 400 Bad Request
        assert response.status_code == 400, "운영시간 외 예약은 차단되어야 합니다"

    def test_reserve_seat_exceeding_daily_limit(self, client, test_token, test_seat, db_session):
        """일일 4시간 초과 예약 시도 - 실패 예상"""
        from app.models import Reservation, ReservationStatus
        from datetime import datetime, timezone

        # 이미 4시간 예약이 있는 상태 생성
        existing = Reservation(
            student_id=202312345,
            seat_id=test_seat.seat_id,
            meeting_room_id=None,
            start_time=datetime(2025, 12, 20, 9, 0, 0, tzinfo=timezone.utc),
            end_time=datetime(2025, 12, 20, 13, 0, 0, tzinfo=timezone.utc),  # 4시간
            status=ReservationStatus.RESERVED
        )
        db_session.add(existing)
        db_session.commit()

        # 추가 2시간 예약 시도 (총 6시간 - 제한 초과)
        response = client.post(
            "/api/reservations/seats",
            json={
                "seat_id": test_seat.seat_id,
                "date": "2025-12-20",
                "start_time": "13:00",
                "end_time": "15:00"
            },
            headers={"Authorization": f"Bearer {test_token}"}
        )

        # 기대: 400 Bad Request (일일 4시간 제한 초과)
        assert response.status_code == 400, "일일 4시간 제한을 초과하면 차단되어야 합니다"


@pytest.mark.integration
@pytest.mark.seat_reservation
class TestRandomSeatReservationEdgeCases:
    """랜덤 좌석 예약 엣지 케이스 - 실패 예상"""

    def test_random_seat_no_available_seats(self, client, test_token, db_session):
        """가용 좌석이 없을 때 랜덤 예약 - 실패 예상"""
        from app.models import Seat, Reservation, ReservationStatus
        from datetime import datetime, timezone

        # 좌석 1개 생성
        seat = Seat(seat_id=1)
        db_session.add(seat)
        db_session.commit()

        # 해당 좌석이 이미 예약됨
        reservation = Reservation(
            student_id=999999999,
            seat_id=1,
            meeting_room_id=None,
            start_time=datetime(2025, 12, 20, 9, 0, 0, tzinfo=timezone.utc),
            end_time=datetime(2025, 12, 20, 11, 0, 0, tzinfo=timezone.utc),
            status=ReservationStatus.RESERVED
        )
        db_session.add(reservation)
        db_session.commit()

        # 동일 시간대 랜덤 예약 시도
        response = client.post(
            "/api/reservations/seats/random",
            json={
                "date": "2025-12-20",
                "start_time": "09:00",
                "end_time": "11:00"
            },
            headers={"Authorization": f"Bearer {test_token}"}
        )

        # 기대: 409 Conflict (가용 좌석 없음)
        assert response.status_code == 409, "가용 좌석이 없으면 409 에러를 반환해야 합니다"


@pytest.mark.integration
@pytest.mark.seat_reservation
class TestSeatReservationConcurrency:
    """동시성 문제 테스트 - 실패 예상"""

    def test_concurrent_seat_reservation_same_seat(self, client, test_token, test_seat):
        """동일 좌석 동시 예약 시도 - 실패 예상 (트랜잭션 격리 미흡)"""
        # 이 테스트는 동시성 처리가 미흡할 경우 실패할 수 있음
        import concurrent.futures

        def reserve_seat():
            return client.post(
                "/api/reservations/seats",
                json={
                    "seat_id": test_seat.seat_id,
                    "date": "2025-12-20",
                    "start_time": "09:00",
                    "end_time": "11:00"
                },
                headers={"Authorization": f"Bearer {test_token}"}
            )

        # 동시에 2개 요청 전송
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future1 = executor.submit(reserve_seat)
            future2 = executor.submit(reserve_seat)

            response1 = future1.result()
            response2 = future2.result()

        # 하나는 성공(201), 하나는 실패(409)여야 함
        status_codes = sorted([response1.status_code, response2.status_code])
        assert status_codes == [201, 409], "동시 예약 시 하나만 성공해야 합니다"


@pytest.mark.integration
@pytest.mark.seat_reservation
class TestSeatReservationBusinessLogic:
    """비즈니스 로직 테스트 - 실패 가능성 있는 케이스"""

    def test_reserve_nonexistent_seat(self, client, test_token):
        """존재하지 않는 좌석 예약 시도"""
        response = client.post(
            "/api/reservations/seats",
            json={
                "seat_id": 999999,  # 존재하지 않는 좌석
                "date": "2025-12-20",
                "start_time": "09:00",
                "end_time": "11:00"
            },
            headers={"Authorization": f"Bearer {test_token}"}
        )

        # 기대: 404 Not Found
        # 실제: 외래키 제약조건 위반 시 500 에러 가능
        assert response.status_code in [400, 404], "존재하지 않는 좌석 예약은 차단되어야 합니다"

    def test_reserve_seat_with_meeting_room_conflict(self, client, test_token, test_seat, db_session):
        """동일 시간대 회의실 예약이 있을 때 좌석 예약 시도"""
        from app.models import MeetingRoom, Reservation, ReservationStatus
        from datetime import datetime, timezone

        # 회의실 생성
        room = MeetingRoom(room_id=1)
        db_session.add(room)
        db_session.commit()

        # 동일 시간대 회의실 예약 생성
        meeting_reservation = Reservation(
            student_id=202312345,
            seat_id=None,
            meeting_room_id=1,
            start_time=datetime(2025, 12, 20, 9, 0, 0, tzinfo=timezone.utc),
            end_time=datetime(2025, 12, 20, 11, 0, 0, tzinfo=timezone.utc),
            status=ReservationStatus.RESERVED
        )
        db_session.add(meeting_reservation)
        db_session.commit()

        # 동일 시간대 좌석 예약 시도
        response = client.post(
            "/api/reservations/seats",
            json={
                "seat_id": test_seat.seat_id,
                "date": "2025-12-20",
                "start_time": "09:00",
                "end_time": "11:00"
            },
            headers={"Authorization": f"Bearer {test_token}"}
        )

        # 기대: 409 Conflict (다른 시설 예약 존재)
        assert response.status_code == 409, "동일 시간대 다른 시설 예약 시 충돌해야 합니다"

    def test_reserve_seat_end_time_before_start_time(self, client, test_token, test_seat):
        """종료 시간이 시작 시간보다 이른 예약 시도"""
        response = client.post(
            "/api/reservations/seats",
            json={
                "seat_id": test_seat.seat_id,
                "date": "2025-12-20",
                "start_time": "11:00",
                "end_time": "09:00"  # 종료 < 시작
            },
            headers={"Authorization": f"Bearer {test_token}"}
        )

        # 기대: 400 Bad Request
        assert response.status_code == 400, "종료 시간이 시작 시간보다 이르면 차단되어야 합니다"

    def test_reserve_seat_same_start_end_time(self, client, test_token, test_seat):
        """시작 시간과 종료 시간이 같은 예약 시도"""
        response = client.post(
            "/api/reservations/seats",
            json={
                "seat_id": test_seat.seat_id,
                "date": "2025-12-20",
                "start_time": "09:00",
                "end_time": "09:00"  # 0시간 예약
            },
            headers={"Authorization": f"Bearer {test_token}"}
        )

        # 기대: 400 Bad Request
        assert response.status_code == 400, "0시간 예약은 차단되어야 합니다"
