"""
constants.py - Application Constants
====================================
This module defines constant values used throughout the application.
"""


class ErrorCode:
    """API Error Code Constants"""

    # Authentication errors
    AUTH_INVALID_STUDENT_ID = "AUTH_INVALID_STUDENT_ID"
    AUTH_UNAUTHORIZED = "AUTH_UNAUTHORIZED"

    # Validation errors
    VALIDATION_ERROR = "VALIDATION_ERROR"

    # Time-related errors
    TIME_OUT_OF_OPERATION_HOURS = "TIME_OUT_OF_OPERATION_HOURS"

    # Reservation conflicts
    RESERVATION_CONFLICT = "RESERVATION_CONFLICT"
    OVERLAP_WITH_OTHER_FACILITY = "OVERLAP_WITH_OTHER_FACILITY"

    # Limit errors
    DAILY_LIMIT_EXCEEDED = "DAILY_LIMIT_EXCEEDED"
    WEEKLY_LIMIT_EXCEEDED = "WEEKLY_LIMIT_EXCEEDED"

    # Meeting room specific
    PARTICIPANT_MIN_NOT_MET = "PARTICIPANT_MIN_NOT_MET"

    # General errors
    NOT_FOUND = "NOT_FOUND"
    FORBIDDEN = "FORBIDDEN"


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
    """Reservation Status Constants"""
    RESERVED = "RESERVED"
    CANCELED = "CANCELED"


class FacilityConstants:
    """Facility Constants"""
    MEETING_ROOM_IDS = [1, 2, 3]
    SEAT_MIN_ID = 1
    SEAT_MAX_ID = 70
