"""
conftest.py - pytest 설정 및 공통 fixture
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone, timedelta, date

from app.main import app
from app.database import Base, get_db
from app.models import User, Seat, MeetingRoom, Reservation, ReservationStatus, ReservationParticipant
# from app.utils.auth import create_access_token

# 테스트용 DB URL (SQLite 메모리 DB)
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"

# KST timezone
KST = timezone(timedelta(hours=9))
UTC = timezone.utc


# --------------------------------------------------------------------------
# Database Fixtures
# --------------------------------------------------------------------------
@pytest.fixture(scope="session")
def test_engine():
    """테스트용 DB 엔진 생성"""
    engine = create_engine(
        SQLALCHEMY_TEST_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(test_engine):
    """각 테스트마다 독립적인 DB 세션 제공"""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    yield session
    session.rollback()
    # 모든 테이블 데이터 삭제 (테스트 격리)
    for table in reversed(Base.metadata.sorted_tables):
        session.execute(table.delete())
    session.commit()
    session.close()


@pytest.fixture(scope="function")
def client(db_session):
    """테스트용 FastAPI 클라이언트"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# --------------------------------------------------------------------------
# User Fixtures 고정물
# --------------------------------------------------------------------------
@pytest.fixture
def test_user(db_session):
    """테스트용 사용자 생성"""
    user = User(
        student_id=202312345,
        last_login_at=datetime.now(UTC)
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_token(test_user):
    """테스트용 인증 토큰 생성"""
    from uuid import uuid4
    token = f"token-{test_user.student_id}-{uuid4().hex}"
    return token


@pytest.fixture
def multiple_users(db_session):
    """여러 테스트 사용자 생성"""
    users = []
    for i in range(202312346, 202312351):  # 5명의 사용자 생성
        user = User(
            student_id=i,
            last_login_at=datetime.now(UTC)
        )
        db_session.add(user)
        users.append(user)

    db_session.commit()
    for user in users:
        db_session.refresh(user)
    return users


# --------------------------------------------------------------------------
# Seat Fixtures
# --------------------------------------------------------------------------
@pytest.fixture
def test_seat(db_session):
    """테스트용 좌석 생성"""
    seat = Seat(
        seat_id=1,
        is_available=True
    )
    db_session.add(seat)
    db_session.commit()
    db_session.refresh(seat)
    return seat


@pytest.fixture
def available_seats(db_session):
    """이용 가능한 좌석 리스트"""
    seats = []
    for seat_id in range(1, 11):  # 좌석 1-10번
        seat = Seat(
            seat_id=seat_id,
            is_available=True
        )
        db_session.add(seat)
        seats.append(seat)

    db_session.commit()
    for seat in seats:
        db_session.refresh(seat)
    return seats


@pytest.fixture
def reserved_seats(db_session):
    """예약된 좌석 리스트"""
    seats = []
    for seat_id in range(11, 16):  # 좌석 11-15번
        seat = Seat(
            seat_id=seat_id,
            is_available=False
        )
        db_session.add(seat)
        seats.append(seat)

    db_session.commit()
    for seat in seats:
        db_session.refresh(seat)
    return seats


# --------------------------------------------------------------------------
# Meeting Room Fixtures
# --------------------------------------------------------------------------
@pytest.fixture
def test_meeting_room(db_session):
    """테스트용 회의실 생성"""
    meeting_room = MeetingRoom(
        room_id=1,
        min_capacity=3,
        max_capacity=6,
        is_available=True
    )
    db_session.add(meeting_room)
    db_session.commit()
    db_session.refresh(meeting_room)
    return meeting_room


@pytest.fixture
def available_meeting_rooms(db_session):
    """이용 가능한 회의실 리스트"""
    rooms = []
    for room_id in range(1, 6):  # 회의실 1-5번
        room = MeetingRoom(
            room_id=room_id,
            min_capacity=3,
            max_capacity=6,
            is_available=True
        )
        db_session.add(room)
        rooms.append(room)

    db_session.commit()
    for room in rooms:
        db_session.refresh(room)
    return rooms


# --------------------------------------------------------------------------
# Reservation Fixtures
# --------------------------------------------------------------------------
@pytest.fixture
def seat_reservation(db_session, test_user, test_seat):
    """좌석 예약 샘플"""
    reservation = Reservation(
        student_id=test_user.student_id,
        seat_id=test_seat.seat_id,
        meeting_room_id=None,
        start_time=datetime(2025, 12, 20, 2, 0, 0, tzinfo=UTC),  # KST 11:00
        end_time=datetime(2025, 12, 20, 4, 0, 0, tzinfo=UTC),    # KST 13:00
        status=ReservationStatus.RESERVED
    )
    db_session.add(reservation)
    db_session.commit()
    db_session.refresh(reservation)
    return reservation


@pytest.fixture
def meeting_room_reservation(db_session, test_user, test_meeting_room):
    """회의실 예약 샘플"""
    reservation = Reservation(
        student_id=test_user.student_id,
        meeting_room_id=test_meeting_room.room_id,
        seat_id=None,
        start_time=datetime(2025, 12, 20, 3, 0, 0, tzinfo=UTC),  # KST 12:00
        end_time=datetime(2025, 12, 20, 5, 0, 0, tzinfo=UTC),    # KST 14:00
        status=ReservationStatus.RESERVED
    )
    db_session.add(reservation)
    db_session.commit()
    db_session.refresh(reservation)
    return reservation


@pytest.fixture
def expired_reservation(db_session, test_user):
    """만료된 예약"""
    # 과거 날짜의 예약
    reservation = Reservation(
        student_id=test_user.student_id,
        seat_id=1,
        meeting_room_id=None,
        start_time=datetime(2025, 12, 18, 2, 0, 0, tzinfo=UTC),
        end_time=datetime(2025, 12, 18, 4, 0, 0, tzinfo=UTC),
        status=ReservationStatus.COMPLETED
    )
    db_session.add(reservation)
    db_session.commit()
    db_session.refresh(reservation)
    return reservation


@pytest.fixture
def canceled_reservation(db_session, test_user):
    """취소된 예약"""
    reservation = Reservation(
        student_id=test_user.student_id,
        seat_id=1,
        meeting_room_id=None,
        start_time=datetime(2025, 12, 21, 2, 0, 0, tzinfo=UTC),
        end_time=datetime(2025, 12, 21, 4, 0, 0, tzinfo=UTC),
        status=ReservationStatus.CANCELED
    )
    db_session.add(reservation)
    db_session.commit()
    db_session.refresh(reservation)
    return reservation


# --------------------------------------------------------------------------
# Time Fixtures
# --------------------------------------------------------------------------
@pytest.fixture
def mock_now():
    """현재 시간 모킹"""
    # 2025-12-20 10:00:00 UTC (KST 19:00)
    return datetime(2025, 12, 20, 10, 0, 0, tzinfo=UTC)


@pytest.fixture
def test_date():
    """테스트용 날짜 (2025-12-20)"""
    return date(2025, 12, 20)


@pytest.fixture
def operation_hours():
    """운영 시간 정보"""
    return {
        "start_hour": 9,   # 오전 9시
        "end_hour": 22,    # 오후 10시
        "timezone": KST
    }
