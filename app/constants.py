"""
constants.py - Application-wide constant definitions.
"""

from enum import Enum


class ErrorCode(str, Enum):
    """API error code definitions."""

    # Common / validation
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    PARTICIPANT_MIN_NOT_MET = "PARTICIPANT_MIN_NOT_MET"

    # Business logic
    RESERVATION_CONFLICT = "RESERVATION_CONFLICT"
    RESERVATION_ALREADY_CANCELED = "RESERVATION_ALREADY_CANCELED"
    USAGE_LIMIT_EXCEEDED = "USAGE_LIMIT_EXCEEDED"
    DAILY_LIMIT_EXCEEDED = "DAILY_LIMIT_EXCEEDED"
    WEEKLY_LIMIT_EXCEEDED = "WEEKLY_LIMIT_EXCEEDED"
    OVERLAP_WITH_OTHER_FACILITY = "OVERLAP_WITH_OTHER_FACILITY"
    AUTH_UNAUTHORIZED = "AUTH_UNAUTHORIZED"
    AUTH_FORBIDDEN = "AUTH_FORBIDDEN"
    SEAT_ALREADY_EXISTS = "SEAT_ALREADY_EXISTS"
    AUTH_INVALID_STUDENT_ID = "AUTH_INVALID_STUDENT_ID"


ERROR_MESSAGES = {
    ErrorCode.VALIDATION_ERROR: "입력 값이 올바르지 않거나 유효하지 않은 요청입니다.",
    ErrorCode.NOT_FOUND: "요청하신 리소스를 찾을 수 없습니다.",
    ErrorCode.INTERNAL_SERVER_ERROR: "서버 내부 오류가 발생했습니다.",
    ErrorCode.PARTICIPANT_MIN_NOT_MET: "회의실 참여자는 최소 3명 이상이어야 합니다.",
    ErrorCode.RESERVATION_CONFLICT: "선택하신 시간대에 이미 예약이 존재합니다.",
    ErrorCode.RESERVATION_ALREADY_CANCELED: "이미 취소된 예약입니다.",
    ErrorCode.USAGE_LIMIT_EXCEEDED: "시설 이용 한도를 초과했습니다.",
    ErrorCode.DAILY_LIMIT_EXCEEDED: "일일 이용 한도를 초과했습니다.",
    ErrorCode.WEEKLY_LIMIT_EXCEEDED: "주간 이용 한도를 초과했습니다.",
    ErrorCode.OVERLAP_WITH_OTHER_FACILITY: "동일 시간대 다른 시설 예약이 존재합니다.",
    ErrorCode.AUTH_UNAUTHORIZED: "로그인이 필요합니다.",
    ErrorCode.AUTH_FORBIDDEN: "접근 권한이 없습니다.",
    ErrorCode.SEAT_ALREADY_EXISTS: "이미 존재하는 좌석입니다.",
    ErrorCode.AUTH_INVALID_STUDENT_ID: "유효하지 않은 학번입니다.",
}


class OperationHours:
    """Operation Hours Constants"""

    START_HOUR = 9
    START_MINUTE = 0
    END_HOUR = 18
    END_MINUTE = 0


class ReservationLimits:
    """Reservation Time Limits (in minutes)"""

    # Meeting room limits
    MEETING_ROOM_SLOT_MINUTES = 60  # 1 hour
    MEETING_ROOM_DAILY_LIMIT_MINUTES = 120  # 2 hours per day
    MEETING_ROOM_WEEKLY_LIMIT_MINUTES = 300  # 5 hours per week
    MEETING_ROOM_MIN_PARTICIPANTS = 3

    # Seat limits
    SEAT_SLOT_MINUTES = 120  # 2 hours
    SEAT_DAILY_LIMIT_MINUTES = 240  # 4 hours per day


class ReservationType:
    """Reservation Type Constants"""

    MEETING_ROOM = "meeting_room"
    SEAT = "seat"


class ReservationStatus:
    """Reservation status constants."""

    RESERVED = "RESERVED"
    IN_USE = "IN_USE"
    COMPLETED = "COMPLETED"
    CANCELED = "CANCELED"


class FacilityConstants:
    """Facility constants."""

    MEETING_ROOM_IDS = [1, 2, 3]
    SEAT_MIN_ID = 1
    SEAT_MAX_ID = 70
