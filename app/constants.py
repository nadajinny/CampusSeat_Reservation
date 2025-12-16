"""
constants.py - Application Constants
====================================
This module defines constant values used throughout the application.
"""
from enum import Enum

class ErrorCode(str, Enum):
    """API 에러 코드 정의"""
    # 1. 공통/유효성
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    
    # 2. 비즈니스 로직
    RESERVATION_CONFLICT = "RESERVATION_CONFLICT"
    USAGE_LIMIT_EXCEEDED = "USAGE_LIMIT_EXCEEDED"
    AUTH_UNAUTHORIZED = "AUTH_UNAUTHORIZED"
    AUTH_FORBIDDEN = "AUTH_FORBIDDEN"
    SEAT_ALREADY_EXISTS = "SEAT_ALREADY_EXISTS"
    AUTH_INVALID_STUDENT = "AUTH_INVALID_STUDENT"

# 기본 에러 메시지 매핑
ERROR_MESSAGES = {
    ErrorCode.VALIDATION_ERROR: "입력 값이 올바르지 않거나 유효하지 않은 요청입니다.",
    ErrorCode.NOT_FOUND: "요청하신 리소스를 찾을 수 없습니다.",
    ErrorCode.INTERNAL_SERVER_ERROR: "서버 내부 오류가 발생했습니다.",
    ErrorCode.RESERVATION_CONFLICT: "선택하신 시간대에 이미 예약이 존재합니다.",
    ErrorCode.USAGE_LIMIT_EXCEEDED: "시설 이용 한도를 초과했습니다.",
    ErrorCode.AUTH_UNAUTHORIZED: "로그인이 필요합니다.",
    ErrorCode.AUTH_FORBIDDEN: "접근 권한이 없습니다.",
    ErrorCode.SEAT_ALREADY_EXISTS: "이미 존재하는 좌석입니다.",
    ErrorCode.AUTH_INVALID_STUDENT: "유효하지 않은 학번입니다.",
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
    """
    Reservation Status Constants

    Status Flow:
    - RESERVED: Initial state when reservation is created
    - IN_USE: User has checked in and is currently using the facility
    - COMPLETED: Reservation time has ended, used successfully
    - CANCELED: Reservation was canceled before use
    """
    RESERVED = "RESERVED"      # Reservation created, waiting for use
    IN_USE = "IN_USE"          # Currently being used
    COMPLETED = "COMPLETED"    # Successfully completed
    CANCELED = "CANCELED"      # Canceled by user


class FacilityConstants:
    """Facility Constants"""
    MEETING_ROOM_IDS = [1, 2, 3]
    SEAT_MIN_ID = 1
    SEAT_MAX_ID = 70
