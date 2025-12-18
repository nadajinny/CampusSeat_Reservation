"""
helpers.py - 테스트 헬퍼 함수
"""
from datetime import datetime, time, timedelta, timezone, date as date_type


UTC = timezone.utc
KST = timezone(timedelta(hours=9))


class TimeHelpers:
    """시간 관련 헬퍼"""

    @staticmethod
    def generate_time_slots(slot_minutes=60, start_hour=9, end_hour=18):
        """시간 슬롯 생성"""
        slots = []
        current_hour = start_hour
        current_minute = 0

        while current_hour < end_hour:
            start = time(hour=current_hour, minute=current_minute)

            # 다음 슬롯 계산
            next_minutes = current_minute + slot_minutes
            next_hour = current_hour + (next_minutes // 60)
            next_minute = next_minutes % 60

            if next_hour > end_hour:
                break

            end = time(hour=next_hour, minute=next_minute)
            slots.append({"start": start, "end": end})

            current_hour = next_hour
            current_minute = next_minute

        return slots

    @staticmethod
    def is_within_operation_hours(time_obj, start_hour=9, end_hour=18):
        """운영 시간 내에 있는지 확인"""
        return start_hour <= time_obj.hour < end_hour

    @staticmethod
    def calculate_duration(start_time, end_time):
        """시작-종료 시간 간격 계산 (분 단위)"""
        if isinstance(start_time, datetime) and isinstance(end_time, datetime):
            delta = end_time - start_time
            return int(delta.total_seconds() / 60)
        else:
            # time 객체인 경우
            start_minutes = start_time.hour * 60 + start_time.minute
            end_minutes = end_time.hour * 60 + end_time.minute
            return end_minutes - start_minutes

    @staticmethod
    def kst_to_utc(kst_datetime):
        """KST를 UTC로 변환"""
        if kst_datetime.tzinfo is None:
            kst_datetime = kst_datetime.replace(tzinfo=KST)
        return kst_datetime.astimezone(UTC)

    @staticmethod
    def utc_to_kst(utc_datetime):
        """UTC를 KST로 변환"""
        if utc_datetime.tzinfo is None:
            utc_datetime = utc_datetime.replace(tzinfo=UTC)
        return utc_datetime.astimezone(KST)

    @staticmethod
    def get_test_datetime(date_str, time_str):
        """테스트용 datetime 객체 생성"""
        # date_str: "2025-12-20", time_str: "14:00"
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        time_obj = datetime.strptime(time_str, "%H:%M").time()
        return datetime.combine(date_obj, time_obj, tzinfo=UTC)


class ValidationHelpers:
    """검증 헬퍼"""

    BLOCKED_STUDENT_IDS = [202099999, 202288888]

    @staticmethod
    def validate_student_id(student_id):
        """학번 유효성 검증 (9자리, 금지된 학번 체크)"""
        if not isinstance(student_id, int):
            return False, "학번은 정수여야 합니다"

        student_id_str = str(student_id)
        if len(student_id_str) != 9:
            return False, "학번은 9자리여야 합니다"

        if student_id in ValidationHelpers.BLOCKED_STUDENT_IDS:
            return False, "금지된 학번입니다"

        return True, None

    @staticmethod
    def validate_time_range(start_time, end_time):
        """시간 범위 유효성 검증"""
        if start_time >= end_time:
            return False, "시작 시간은 종료 시간보다 빨라야 합니다"

        return True, None

    @staticmethod
    def validate_participants(participants, min_count=3):
        """참여자 유효성 검증 (최소 인원, 중복 체크)"""
        if len(participants) < min_count:
            return False, f"최소 {min_count}명의 참여자가 필요합니다"

        # 중복 체크
        student_ids = [p["student_id"] if isinstance(p, dict) else p for p in participants]
        if len(student_ids) != len(set(student_ids)):
            return False, "중복된 참여자가 있습니다"

        return True, None

    @staticmethod
    def validate_date_format(date_str):
        """날짜 형식 검증 (YYYY-MM-DD)"""
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True, None
        except ValueError:
            return False, "날짜 형식이 올바르지 않습니다 (YYYY-MM-DD)"


class APIHelpers:
    """API 테스트 헬퍼"""

    @staticmethod
    def get_auth_headers(token):
        """인증 헤더 생성"""
        return {"Authorization": f"Bearer {token}"}

    @staticmethod
    def make_reservation_request(facility_type, **kwargs):
        """예약 요청 데이터 생성"""
        base_request = {
            "date": kwargs.get("date", "2025-12-20"),
            "start_time": kwargs.get("start_time", "10:00"),
            "end_time": kwargs.get("end_time", "12:00")
        }

        if facility_type == "seat":
            base_request["seat_id"] = kwargs.get("seat_id", 1)
        elif facility_type == "meeting_room":
            base_request["room_id"] = kwargs.get("room_id", 1)
            base_request["participant_ids"] = kwargs.get("participant_ids", [202312346, 202312347, 202312348])

        return base_request

    @staticmethod
    def parse_response(response):
        """응답 파싱 및 검증"""
        try:
            data = response.json()
            return {
                "status_code": response.status_code,
                "is_success": data.get("is_success"),
                "code": data.get("code"),
                "message": data.get("message"),
                "payload": data.get("payload")
            }
        except Exception as e:
            return {
                "status_code": response.status_code,
                "error": str(e),
                "raw_content": response.text
            }


class DatabaseHelpers:
    """데이터베이스 헬퍼"""

    @staticmethod
    def cleanup_reservations(db_session):
        """테스트 후 예약 데이터 정리"""
        from app.models import Reservation, ReservationParticipant

        db_session.query(ReservationParticipant).delete()
        db_session.query(Reservation).delete()
        db_session.commit()

    @staticmethod
    def get_reservation_count(db_session, student_id=None):
        """예약 개수 조회"""
        from app.models import Reservation

        query = db_session.query(Reservation)
        if student_id:
            query = query.filter(Reservation.student_id == student_id)
        return query.count()

    @staticmethod
    def create_test_data(db_session):
        """테스트용 기본 데이터 생성"""
        from app.models import User, Seat, MeetingRoom

        # 사용자 생성
        user = User(student_id=202312345, last_login_at=datetime.now(UTC))
        db_session.add(user)

        # 좌석 생성
        for seat_id in range(1, 11):
            seat = Seat(seat_id=seat_id, is_available=True)
            db_session.add(seat)

        # 회의실 생성
        for room_id in range(1, 4):
            room = MeetingRoom(
                room_id=room_id,
                min_capacity=3,
                max_capacity=6,
                is_available=True
            )
            db_session.add(room)

        db_session.commit()
