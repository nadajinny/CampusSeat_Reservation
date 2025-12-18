"""
factories.py - 테스트 데이터 팩토리
"""
from datetime import datetime, timedelta


class UserFactory:
    """사용자 테스트 데이터 생성"""

    @staticmethod
    def create_user(student_id=202312345, name="홍길동"):
        """단일 사용자 생성"""
        pass

    @staticmethod
    def create_users_batch(count=5):
        """여러 사용자 일괄 생성"""
        pass

    @staticmethod
    def create_blocked_user():
        """금지된 학번 사용자 (202099999 또는 202288888)"""
        pass


class SeatFactory:
    """좌석 테스트 데이터 생성"""

    @staticmethod
    def create_seat(seat_id=1):
        """단일 좌석 생성"""
        pass

    @staticmethod
    def create_seats_batch(start_id=1, end_id=10):
        """여러 좌석 일괄 생성"""
        pass


class MeetingRoomFactory:
    """회의실 테스트 데이터 생성"""

    @staticmethod
    def create_meeting_room(room_id=1):
        """단일 회의실 생성"""
        pass

    @staticmethod
    def create_all_meeting_rooms():
        """모든 회의실 생성 (1, 2, 3)"""
        pass


class ReservationFactory:
    """예약 테스트 데이터 생성"""

    @staticmethod
    def create_seat_reservation(student_id, seat_id, date, start_time, end_time, status="RESERVED"):
        """좌석 예약 생성"""
        pass

    @staticmethod
    def create_meeting_room_reservation(student_id, room_id, date, start_time, end_time,
                                       participants=None, status="RESERVED"):
        """회의실 예약 생성"""
        pass

    @staticmethod
    def create_reservation_with_participants(student_id, room_id, participant_count=3):
        """참여자 포함 회의실 예약 생성"""
        pass

    @staticmethod
    def create_canceled_reservation(student_id, facility_type="seat"):
        """취소된 예약 생성"""
        pass

    @staticmethod
    def create_completed_reservation(student_id, facility_type="seat"):
        """완료된 예약 생성"""
        pass

    @staticmethod
    def create_in_use_reservation(student_id, facility_type="seat"):
        """사용 중인 예약 생성"""
        pass


class ParticipantFactory:
    """참여자 테스트 데이터 생성"""

    @staticmethod
    def create_participant(student_id=202312345, name="홍길동"):
        """단일 참여자 생성"""
        pass

    @staticmethod
    def create_participants(count=3):
        """여러 참여자 생성"""
        pass

    @staticmethod
    def create_duplicate_participants():
        """중복된 학번을 가진 참여자 리스트"""
        pass
