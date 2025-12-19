"""
factories.py - 테스트 데이터 팩토리
"""
from datetime import datetime, timedelta, timezone, date
from app.models import User, Seat, MeetingRoom, Reservation, ReservationStatus, ReservationParticipant

UTC = timezone.utc


class UserFactory:
    """사용자 테스트 데이터 생성"""

    @staticmethod
    def create_user(student_id=202312345, name="홍길동"):
        """단일 사용자 생성"""
        return User(
            student_id=student_id,
            last_login_at=datetime.now(UTC)
        )

    @staticmethod
    def create_users_batch(count=5):
        """여러 사용자 일괄 생성"""
        users = []
        for i in range(count):
            user = User(
                student_id=202312345 + i,
                last_login_at=datetime.now(UTC)
            )
            users.append(user)
        return users

    @staticmethod
    def create_blocked_user():
        """금지된 학번 사용자 (202099999 또는 202288888)"""
        return User(
            student_id=202099999,
            last_login_at=datetime.now(UTC)
        )


class SeatFactory:
    """좌석 테스트 데이터 생성"""

    @staticmethod
    def create_seat(seat_id=1):
        """단일 좌석 생성"""
        return Seat(
            seat_id=seat_id,
            is_available=True
        )

    @staticmethod
    def create_seats_batch(start_id=1, end_id=10):
        """여러 좌석 일괄 생성"""
        seats = []
        for seat_id in range(start_id, end_id + 1):
            seat = Seat(
                seat_id=seat_id,
                is_available=True
            )
            seats.append(seat)
        return seats


class MeetingRoomFactory:
    """회의실 테스트 데이터 생성"""

    @staticmethod
    def create_meeting_room(room_id=1):
        """단일 회의실 생성"""
        return MeetingRoom(
            room_id=room_id,
            min_capacity=3,
            max_capacity=6,
            is_available=True
        )

    @staticmethod
    def create_all_meeting_rooms():
        """모든 회의실 생성 (1, 2, 3)"""
        rooms = []
        for room_id in range(1, 4):  # 1, 2, 3번 회의실
            room = MeetingRoom(
                room_id=room_id,
                min_capacity=3,
                max_capacity=6,
                is_available=True
            )
            rooms.append(room)
        return rooms


class ReservationFactory:
    """예약 테스트 데이터 생성"""

    @staticmethod
    def create_seat_reservation(student_id, seat_id, date, start_time, end_time, status="RESERVED"):
        """좌석 예약 생성"""
        start_dt = datetime.combine(date, start_time, tzinfo=UTC)
        end_dt = datetime.combine(date, end_time, tzinfo=UTC)

        return Reservation(
            student_id=student_id,
            seat_id=seat_id,
            meeting_room_id=None,
            start_time=start_dt,
            end_time=end_dt,
            status=ReservationStatus[status]
        )

    @staticmethod
    def create_meeting_room_reservation(student_id, room_id, date, start_time, end_time,
                                       participants=None, status="RESERVED"):
        """회의실 예약 생성"""
        start_dt = datetime.combine(date, start_time, tzinfo=UTC)
        end_dt = datetime.combine(date, end_time, tzinfo=UTC)

        return Reservation(
            student_id=student_id,
            meeting_room_id=room_id,
            seat_id=None,
            start_time=start_dt,
            end_time=end_dt,
            status=ReservationStatus[status]
        )

    @staticmethod
    def create_reservation_with_participants(student_id, room_id, participant_count=3):
        """참여자 포함 회의실 예약 생성"""
        # 내일 오전 10시-12시 예약
        tomorrow = date.today() + timedelta(days=1)
        start_dt = datetime.combine(tomorrow, datetime.min.time().replace(hour=1), tzinfo=UTC)  # UTC 01:00 = KST 10:00
        end_dt = datetime.combine(tomorrow, datetime.min.time().replace(hour=3), tzinfo=UTC)    # UTC 03:00 = KST 12:00

        return Reservation(
            student_id=student_id,
            meeting_room_id=room_id,
            seat_id=None,
            start_time=start_dt,
            end_time=end_dt,
            status=ReservationStatus.RESERVED
        )

    @staticmethod
    def create_canceled_reservation(student_id, facility_type="seat"):
        """취소된 예약 생성"""
        tomorrow = date.today() + timedelta(days=1)
        start_dt = datetime.combine(tomorrow, datetime.min.time().replace(hour=2), tzinfo=UTC)
        end_dt = datetime.combine(tomorrow, datetime.min.time().replace(hour=4), tzinfo=UTC)

        if facility_type == "seat":
            return Reservation(
                student_id=student_id,
                seat_id=1,
                meeting_room_id=None,
                start_time=start_dt,
                end_time=end_dt,
                status=ReservationStatus.CANCELED
            )
        else:
            return Reservation(
                student_id=student_id,
                meeting_room_id=1,
                seat_id=None,
                start_time=start_dt,
                end_time=end_dt,
                status=ReservationStatus.CANCELED
            )

    @staticmethod
    def create_completed_reservation(student_id, facility_type="seat"):
        """완료된 예약 생성"""
        yesterday = date.today() - timedelta(days=1)
        start_dt = datetime.combine(yesterday, datetime.min.time().replace(hour=2), tzinfo=UTC)
        end_dt = datetime.combine(yesterday, datetime.min.time().replace(hour=4), tzinfo=UTC)

        if facility_type == "seat":
            return Reservation(
                student_id=student_id,
                seat_id=1,
                meeting_room_id=None,
                start_time=start_dt,
                end_time=end_dt,
                status=ReservationStatus.COMPLETED
            )
        else:
            return Reservation(
                student_id=student_id,
                meeting_room_id=1,
                seat_id=None,
                start_time=start_dt,
                end_time=end_dt,
                status=ReservationStatus.COMPLETED
            )

    @staticmethod
    def create_in_use_reservation(student_id, facility_type="seat"):
        """사용 중인 예약 생성"""
        now = datetime.now(UTC)
        start_dt = now - timedelta(hours=1)
        end_dt = now + timedelta(hours=1)

        if facility_type == "seat":
            return Reservation(
                student_id=student_id,
                seat_id=1,
                meeting_room_id=None,
                start_time=start_dt,
                end_time=end_dt,
                status=ReservationStatus.IN_USE
            )
        else:
            return Reservation(
                student_id=student_id,
                meeting_room_id=1,
                seat_id=None,
                start_time=start_dt,
                end_time=end_dt,
                status=ReservationStatus.IN_USE
            )


class ParticipantFactory:
    """참여자 테스트 데이터 생성"""

    @staticmethod
    def create_participant(student_id=202312345, name="홍길동"):
        """단일 참여자 생성"""
        return {
            "student_id": student_id,
            "name": name
        }

    @staticmethod
    def create_participants(count=3):
        """여러 참여자 생성"""
        participants = []
        for i in range(count):
            participant = {
                "student_id": 202312346 + i,
                "name": f"참여자{i+1}"
            }
            participants.append(participant)
        return participants

    @staticmethod
    def create_duplicate_participants():
        """중복된 학번을 가진 참여자 리스트"""
        return [
            {"student_id": 202312346, "name": "참여자1"},
            {"student_id": 202312346, "name": "참여자1_중복"},
            {"student_id": 202312347, "name": "참여자2"}
        ]
