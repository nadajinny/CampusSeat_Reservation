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

### **backend/pytest.ini**

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

### **7. 구축된 테스팅 환경**

### **7.1 테스팅 라이브러리**

**backend/requirements-test.txt**

```
pytest==7.4.3              # 테스트 프레임워크
pytest-cov==4.1.0          # 코드 커버리지 측정
pytest-asyncio==0.21.1     # 비동기 테스트 지원
pytest-mock==3.12.0        # Mock 객체 지원
httpx==0.25.2              # TestClient를 위한 HTTP 클라이언트
faker==20.1.0              # 테스트 데이터 생성
```

**주요 라이브러리 설명:**
- **pytest**: Python 테스트 프레임워크의 사실상 표준
- **pytest-cov**: 코드 커버리지 리포트 생성 (목표: 80% 이상)
- **pytest-asyncio**: FastAPI의 async 함수 테스트 지원
- **pytest-mock**: unittest.mock을 pytest fixture로 제공
- **httpx**: FastAPI TestClient의 기반 HTTP 클라이언트
- **faker**: 랜덤 테스트 데이터 생성 (사용자명, 이메일 등)

### **7.2 물리적 환경 구성**

**데이터베이스 설정:**
```python
# SQLite 테스트 데이터베이스
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"

# 테스트용 엔진 및 세션 설정
- 세션 스코프 엔진: 테스트 실행 시작 시 생성, 종료 시 삭제
- 함수 스코프 세션: 각 테스트마다 독립적인 세션 생성
- 자동 롤백: 각 테스트 종료 시 DB 변경사항 롤백 (격리 보장)
```

**Fixture 아키텍처:**
```python
# conftest.py에 구현된 13개 fixture

[Database Fixtures]
- test_engine (scope=session): 테스트 DB 엔진
- db_session (scope=function): 테스트 세션 (자동 롤백)
- client (scope=function): FastAPI TestClient

[User Fixtures]
- test_user: 기본 테스트 사용자 (student_id=202312345)
- test_token: 테스트용 인증 토큰
- multiple_users: 다수의 사용자 생성

[Seat Fixtures]
- test_seat: 단일 좌석 생성
- available_seats: 사용 가능한 좌석 리스트
- reserved_seats: 예약된 좌석 리스트

[Meeting Room Fixtures]
- test_meeting_room: 단일 회의실 생성
- available_meeting_rooms: 사용 가능한 회의실 리스트

[Reservation Fixtures]
- seat_reservation: 좌석 예약 샘플
- meeting_room_reservation: 회의실 예약 샘플
- expired_reservation: 만료된 예약
- canceled_reservation: 취소된 예약

[Time Fixtures]
- mock_now: 현재 시간 모킹
- test_date: 테스트용 날짜 (2025-12-20)
- operation_hours: 운영 시간 설정 (9:00-22:00)
```

**유틸리티 모듈:**
```python
# tests/utils/ 에 구현된 헬퍼 클래스

[factories.py - 테스트 데이터 팩토리]
- UserFactory: 사용자 생성
- SeatFactory: 좌석 생성
- MeetingRoomFactory: 회의실 생성
- ReservationFactory: 예약 생성 (좌석/회의실)
- ParticipantFactory: 참여자 생성

[assertions.py - 커스텀 Assertion]
- ReservationAssertions: 예약 검증 함수
  * assert_reservation_created
  * assert_reservation_canceled
  * assert_time_conflict
- ResponseAssertions: API 응답 검증
  * assert_success_response
  * assert_error_response
- StatusAssertions: 상태 조회 검증
  * assert_slot_available
  * assert_slot_reserved

[helpers.py - 유틸리티 함수]
- TimeHelpers: 시간 관련 헬퍼
  * generate_time_slots: 시간 슬롯 생성
  * calculate_duration: 시간 계산
  * kst_to_utc, utc_to_kst: 타임존 변환
- ValidationHelpers: 검증 헬퍼
  * validate_date_format
  * validate_time_range
- APIHelpers: API 테스트 헬퍼
  * make_auth_header
- DatabaseHelpers: DB 헬퍼
  * clear_all_tables
```

### **7.3 테스팅 정책**

**테스트 격리 전략:**
1. **세션 격리**: 각 테스트는 독립적인 DB 세션 사용
2. **자동 롤백**: 테스트 종료 시 모든 DB 변경사항 자동 롤백
3. **Fixture 스코프**:
   - `session`: 테스트 실행당 1회 생성 (test_engine)
   - `function`: 테스트 함수당 1회 생성 (db_session, fixtures)

**타임존 처리:**
- **저장**: 모든 datetime은 UTC로 저장
- **표시**: 비즈니스 로직은 KST (UTC+9) 기준
- **변환**: TimeHelpers.kst_to_utc / utc_to_kst 사용

**테스트 마커 사용:**
```bash
# backend/pytest.ini에 정의된 마커
@pytest.mark.unit          # 단위 테스트
@pytest.mark.integration   # 통합 테스트
@pytest.mark.auth          # 인증 관련
@pytest.mark.seat          # 좌석 관련
@pytest.mark.meeting_room  # 회의실 관련
@pytest.mark.reservation   # 예약 관련
@pytest.mark.status        # 상태 조회 관련
@pytest.mark.slow          # 느린 테스트 (통합 테스트)
```

**테스트 실행 명령어:**
```bash
# backend 디렉터리에서 실행
cd backend

# 전체 테스트 실행
pytest

# 단위 테스트만 실행
pytest -m unit

# 통합 테스트만 실행
pytest -m integration

# 특정 모듈 테스트
pytest tests/unit/test_auth.py

# 커버리지 리포트 생성
pytest --cov=app --cov-report=html

# 특정 테스트 함수 실행
pytest tests/unit/test_auth.py::TestLoginValidation::test_valid_student_id_login

# 실패한 테스트만 재실행
pytest --lf

# 느린 테스트 제외
pytest -m "not slow"
```

**코드 커버리지 목표:**
- **목표**: 80% 이상
- **우선순위**: Service 계층 100% 커버리지 목표
- **측정 방법**: pytest-cov 플러그인 사용
- **리포트**: HTML 형식으로 생성하여 브라우저에서 확인

### **7.4 구현 현황**

**단위 테스트 (50개 테스트 메서드):**

1. **test_reservation_service.py** (23개)
   - TestReservationQuery: 4개
   - TestReservationCancellation: 6개
   - TestReservationCancellationResponse: 4개
   - TestReservationConflictDetection: 3개
   - TestReservationStateTransition: 3개
   - TestFacilityOverlapValidation: 3개

2. **test_auth.py** (11개)
   - TestLoginValidation: 5개
   - TestTokenGeneration: 2개
   - TestTokenValidation: 3개

3. **test_status_service.py** (16개)
   - TestMeetingRoomStatusQuery: 5개
   - TestSeatStatusQuery: 5개
   - TestAvailableSlotCalculation: 3개
   - TestDateValidation: 4개

**통합 테스트 (구조만 생성, 미구현):**
- test_auth_api.py (11개 메서드 구조)
- test_seat_api.py (13개 메서드 구조)
- test_meeting_room_api.py (9개 메서드 구조)
- test_reservation_api.py (9개 메서드 구조)
- test_status_api.py (6개 메서드 구조)

**테스트 구현 상태:**
- ✅ conftest.py: 13개 fixture 구현 완료
- ✅ utils/: assertions, factories, helpers 구현 완료
- ✅ unit/: 50개 단위 테스트 구현 완료
- ⏳ integration/: 구조만 생성 (기능 완료 후 구현 예정)

### **7.5 테스트 실행 예시**

**정상 케이스:**
```python
def test_valid_student_id_login(self, db_session):
    """유효한 학번으로 로그인 성공"""
    valid_student_id = 202312345

    # 실행
    user = user_service.login_student(db_session, valid_student_id)

    # 검증
    assert user is not None
    assert user.student_id == valid_student_id
    assert user.last_login_at is not None
```

**예외 케이스:**
```python
def test_invalid_student_id_202099999(self, db_session):
    """금지된 학번 202099999 로그인 실패"""
    blocked_id = 202099999

    # 실행 및 검증
    with pytest.raises(BusinessException) as exc_info:
        user_service.login_student(db_session, blocked_id)

    assert exc_info.value.code == ErrorCode.AUTH_INVALID_STUDENT_ID
```

### **8. 추가 권장 사항**

1. **테스트 격리**: 각 테스트는 독립적으로 실행 가능해야 함 (fixture 활용)
2. **모킹**: 외부 의존성(DB, 시간) 모킹 전략 수립
3. **커버리지**: pytest-cov 플러그인 사용 권장 (목표: 80% 이상)
