## **pytest 테스트 구조 계획**

### **1. 테스트 폴더 구조**

**plaintext**

```
tests/
├── __init__.py                    # 테스트 패키지 초기화
├── conftest.py                    # pytest 설정 및 공통 fixture
│
├── unit/                          # 단위 테스트
│   ├── __init__.py
│   ├── test_auth.py               # 인증 로직 테스트
│   ├── test_seat_service.py       # 좌석 서비스 테스트
│   ├── test_meeting_room_service.py  # 회의실 서비스 테스트
│   ├── test_reservation_service.py   # 예약 서비스 테스트
│   ├── test_status_service.py        # 상태 조회 서비스 테스트
│   └── test_user_service.py          # 사용자 서비스 테스트
│
├── integration/                   # 통합 테스트
│   ├── __init__.py
│   ├── test_auth_api.py           # 인증 API 통합 테스트
│   ├── test_seat_api.py           # 좌석 API 통합 테스트
│   ├── test_meeting_room_api.py   # 회의실 API 통합 테스트
│   ├── test_reservation_api.py    # 예약 관리 API 통합 테스트
│   └── test_status_api.py         # 상태 조회 API 통합 테스트
│
├── fixtures/                      # 테스트 데이터 및 헬퍼
│   ├── __init__.py
│   ├── database.py                # DB fixture (테스트용 DB 설정)
│   ├── users.py                   # 사용자 관련 fixture
│   ├── seats.py                   # 좌석 관련 fixture
│   ├── meeting_rooms.py           # 회의실 관련 fixture
│   └── reservations.py            # 예약 관련 fixture
│
└── utils/                         # 테스트 유틸리티
    ├── __init__.py
    ├── assertions.py              # 커스텀 assertion 함수
    ├── factories.py               # 테스트 데이터 팩토리
    └── helpers.py                 # 테스트 헬퍼 함수

```

### **2. 기능별 테스트 클래스 구조**

### **2.1 인증 테스트 (`tests/unit/test_auth.py`)**

**python**

```python
class TestUserService:
    """사용자 서비스 테스트"""

class TestLoginValidation:
    """로그인 검증 로직 테스트"""

class TestTokenGeneration:
    """토큰 생성 로직 테스트"""

class TestTokenValidation:
    """토큰 검증 로직 테스트"""

```

### **2.2 좌석 예약 테스트 (`tests/unit/test_seat_service.py`)**

**python**

```python
class TestSeatQuery:
    """좌석 조회 로직 테스트"""

class TestSeatReservationCreation:
    """좌석 예약 생성 검증 테스트"""

class TestRandomSeatAssignment:
    """랜덤 좌석 배정 로직 테스트"""

class TestSeatDailyLimitValidation:
    """좌석 일일 한도 검증 테스트"""

class TestSeatTimeSlotValidation:
    """좌석 시간대 검증 테스트"""

```

### **2.3 회의실 예약 테스트 (`tests/unit/test_meeting_room_service.py`)**

**python**

```python
class TestMeetingRoomQuery:
    """회의실 조회 로직 테스트"""

class TestMeetingRoomReservationCreation:
    """회의실 예약 생성 검증 테스트"""

class TestParticipantValidation:
    """참여자 검증 로직 테스트"""

class TestMeetingRoomDailyLimitValidation:
    """회의실 일일 한도 검증 테스트"""

class TestMeetingRoomWeeklyLimitValidation:
    """회의실 주간 한도 검증 테스트"""

class TestMeetingRoomConflictValidation:
    """회의실 예약 충돌 검증 테스트"""

```

### **2.4 예약 관리 테스트 (`tests/unit/test_reservation_service.py`)**

**python**

```python
class TestReservationQuery:
    """예약 조회 로직 테스트"""

class TestReservationCancellation:
    """예약 취소 검증 테스트"""

class TestReservationUpdate:
    """예약 수정 검증 테스트"""

class TestReservationConflictDetection:
    """예약 충돌 감지 로직 테스트"""

class TestReservationStateTransition:
    """예약 상태 전이 로직 테스트"""

```

### **2.5 상태 조회 테스트 (`tests/unit/test_status_service.py`)**

**python**

```python
class TestAvailableSlotCalculation:
    """예약 가능 시간대 계산 로직 테스트"""

class TestDateValidation:
    """날짜 검증 로직 테스트"""

```

### **3. conftest.py 구성**

**python**

```python
# 주요 fixture 목록 (실제 코드는 작성하지 않음)
class DatabaseFixtures:
    """데이터베이스 관련 fixture"""
    # db_session: 테스트용 DB 세션
    # test_engine: 테스트용 DB 엔진
    # init_test_db: 테스트 DB 초기화
class UserFixtures:
    """사용자 관련 fixture"""
    # test_user: 테스트용 사용자
    # test_token: 테스트용 인증 토큰
    # multiple_users: 여러 사용자 생성
class SeatFixtures:
    """좌석 관련 fixture"""
    # test_seat: 테스트용 좌석
    # available_seats: 이용 가능 좌석 리스트
    # reserved_seats: 예약된 좌석 리스트
class MeetingRoomFixtures:
    """회의실 관련 fixture"""
    # test_meeting_room: 테스트용 회의실
    # available_meeting_rooms: 이용 가능 회의실 리스트
class ReservationFixtures:
    """예약 관련 fixture"""
    # seat_reservation: 좌석 예약 샘플
    # meeting_room_reservation: 회의실 예약 샘플
    # expired_reservation: 만료된 예약
class TimeFixtures:
    """시간 관련 fixture"""
    # mock_now: 현재 시간 모킹
    # test_date: 테스트용 날짜

```

### **4. 테스트 유틸리티 구조**

### **4.1 assertions.py**

**python**

```python
class ReservationAssertions:
    """예약 관련 검증 함수"""
    # assert_reservation_created
    # assert_reservation_canceled
    # assert_time_conflict
    # assert_limit_exceeded
class ResponseAssertions:
    """API 응답 검증 함수"""
    # assert_success_response
    # assert_error_response
    # assert_error_code

```

### **4.2 factories.py**

**python**

```python
class UserFactory:
    """사용자 테스트 데이터 생성"""
    # create_user
    # create_users_batch
class ReservationFactory:
    """예약 테스트 데이터 생성"""
    # create_seat_reservation
    # create_meeting_room_reservation
    # create_reservation_with_participants

```

### **4.3 helpers.py**

**python**

```python
class TimeHelpers:
    """시간 관련 헬퍼"""
    # generate_time_slots
    # is_within_operation_hours
    # calculate_duration
class ValidationHelpers:
    """검증 헬퍼"""
    # validate_student_id
    # validate_time_range
    # validate_participants

```

### **5. 테스트 범위**

### **5.1 단위 테스트 (unit/)**

- **목적**: 각 서비스 로직의 개별 함수/메서드 검증
- **범위**:
- 입력값 검증 (유효/무효 케이스)
- 비즈니스 로직 정확성
- 예외 발생 조건
- 경계값 테스트

### **5.2 통합 테스트 (integration/)**

- **목적**: API 엔드포인트 전체 흐름 검증
- **범위**:
- HTTP 요청/응답 검증
- 인증/권한 검증
- 데이터베이스 상태 변화
- 에러 응답 형식

### **6. pytest 설정 파일**

### **pytest.ini**

**ini**

```
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --strict-markers
    --tb=short
markers =
    unit: 단위 테스트
    integration: 통합 테스트
    auth: 인증 관련 테스트
    seat: 좌석 관련 테스트
    meeting_room: 회의실 관련 테스트
    reservation: 예약 관련 테스트

```

### **7. 추가 권장 사항**

1. **테스트 격리**: 각 테스트는 독립적으로 실행 가능해야 함 (fixture 활용)
2. **모킹**: 외부 의존성(DB, 시간) 모킹 전략 수립
3. **커버리지**: pytest-cov 플러그인 사용 권장 (목표: 80% 이상)