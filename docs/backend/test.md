# 백엔드 테스트 문서

## 1. 테스트 구조 개요

### 1.1 테스트 폴더 구조

```
tests/
├── __init__.py                       # 테스트 패키지 초기화
├── conftest.py                       # pytest 설정 및 공통 fixture
│
├── unit/                             # 단위 테스트
│   ├── __init__.py
│   ├── test_auth.py                  # 인증 로직 테스트
│   ├── test_seat_service.py          # 좌석 서비스 테스트
│   ├── test_meeting_room_service.py  # 회의실 서비스 테스트
│   ├── test_reservation_service.py   # 예약 서비스 테스트
│   ├── test_reservation_validation.py # 예약 검증 테스트
│   └── test_status_service.py        # 상태 조회 서비스 테스트
│
├── integration/                      # 통합 테스트
│   ├── __init__.py
│   ├── test_auth_api.py              # 인증 API 통합 테스트
│   ├── test_seat_api.py              # 좌석 API 통합 테스트
│   ├── test_seat_reservation_api.py  # 좌석 예약 상세 테스트
│   ├── test_meeting_room_api.py      # 회의실 API 통합 테스트
│   ├── test_reservation_api.py       # 예약 관리 API 통합 테스트
│   └── test_status_api.py            # 상태 조회 API 통합 테스트
│
├── fixtures/                         # 테스트 데이터 및 헬퍼
│   ├── __init__.py
│   ├── database.py                   # DB fixture
│   ├── users.py                      # 사용자 관련 fixture
│   ├── seats.py                      # 좌석 관련 fixture
│   ├── meeting_rooms.py              # 회의실 관련 fixture
│   └── reservations.py               # 예약 관련 fixture
│
└── utils/                            # 테스트 유틸리티
    ├── __init__.py
    ├── assertions.py                 # 커스텀 assertion 함수
    ├── factories.py                  # 테스트 데이터 팩토리
    └── helpers.py                    # 테스트 헬퍼 함수
```

### 1.2 테스트 분류

| 분류 | 목적 | 범위 |
|------|------|------|
| **단위 테스트** | 개별 서비스 로직 검증 | 입력값 검증, 비즈니스 로직, 예외 처리 |
| **통합 테스트** | API 엔드포인트 전체 흐름 검증 | HTTP 요청/응답, 인증, DB 상태 변화 |

---

## 2. HTTP 상태 코드 및 에러 코드 정리

### 2.1 성공 응답 코드

| HTTP 상태 코드 | 의미 | 사용 사례 |
|---------------|------|----------|
| `200 OK` | 요청 성공 | 조회, 취소 성공 |
| `201 Created` | 리소스 생성 성공 | 예약 생성 성공 |

### 2.2 에러 응답 코드

| HTTP 상태 코드 | ErrorCode | 설명 | 발생 사례 |
|---------------|-----------|------|----------|
| `400` | `VALIDATION_ERROR` | 입력값 검증 실패 | 잘못된 학번 형식, 시간 범위 오류, 2시간/1시간 단위 위반 |
| `400` | `AUTH_UNAUTHORIZED` | 인증 실패 | 토큰 없음, 잘못된 토큰 |
| `400` | `AUTH_INVALID_STUDENT_ID` | 금지된 학번 | 202099999, 202288888 |
| `400` | `DAILY_LIMIT_EXCEEDED` | 일일 사용 한도 초과 | 좌석 240분/일, 회의실 120분/일 초과 |
| `400` | `WEEKLY_LIMIT_EXCEEDED` | 주간 사용 한도 초과 | 회의실 300분/주 초과 |
| `400` | `RESERVATION_ALREADY_CANCELED` | 이미 취소된 예약 | 중복 취소 시도 |
| `400` | `NOT_FOUND` | 리소스 없음 | 존재하지 않는 예약/좌석 |
| `400` | `SEAT_NOT_AVAILABLE` | 좌석 이용 불가 | is_available=false인 좌석 |
| `403` | `AUTH_FORBIDDEN` | 권한 없음 | 다른 사용자 예약 취소, IN_USE/COMPLETED 상태 취소 |
| `409` | `RESERVATION_CONFLICT` | 예약 충돌 | 같은 좌석/회의실 동시간 예약 |
| `409` | `OVERLAP_WITH_OTHER_FACILITY` | 다른 시설과 중복 | 좌석 예약 중 회의실 예약 시도 (또는 반대) |
| `409` | `PARTICIPANT_ALREADY_RESERVED` | 참가자 중복 예약 | 참가자가 이미 다른 예약에 포함됨 |

---

## 3. 공통 응답 형식

### 3.1 표준 응답 구조

```json
{
  "is_success": boolean,
  "code": null | "ERROR_CODE",
  "payload": object | array | null
}
```

### 3.2 예약 생성 응답

```json
{
  "is_success": true,
  "code": null,
  "payload": {
    "reservation_id": 1,
    "type": "seat",
    "date": "2025-12-20",
    "start_time": "10:00",
    "end_time": "12:00",
    "seat_id": 1,
    "room_id": null,
    "status": "RESERVED"
  }
}
```

### 3.3 에러 응답

```json
{
  "is_success": false,
  "code": "DAILY_LIMIT_EXCEEDED",
  "payload": null
}
```

---

## 4. 테스트 Fixture 설정 (conftest.py)

### 4.1 데이터베이스 Fixture

| Fixture | Scope | 설명 |
|---------|-------|------|
| `test_engine` | session | SQLite 메모리 DB 엔진 |
| `db_session` | function | 각 테스트용 독립적 DB 세션 |
| `client` | function | FastAPI TestClient |

### 4.2 사용자 Fixture

| Fixture | 설명 | 값 |
|---------|------|-----|
| `test_user` | 기본 테스트 사용자 | student_id: 202312345 |
| `test_token` | 테스트용 JWT 토큰 | token-{student_id}-{uuid} |
| `multiple_users` | 다수의 테스트 사용자 | student_id: 202312346~202312355 (10명) |

### 4.3 시설물 Fixture

| Fixture | 설명 | 상세 |
|---------|------|------|
| `test_seat` | 단일 좌석 | ID: 1 |
| `available_seats` | 가용 좌석 | ID: 1~10 (10개) |
| `reserved_seats` | 예약된 좌석 | ID: 11~15 (5개) |
| `test_meeting_room` | 단일 회의실 | ID: 1, 용량: 3~6명 |
| `available_meeting_rooms` | 가용 회의실 | ID: 1~3 (3개), 용량: 3~6명 |

### 4.4 예약 Fixture

| Fixture | 설명 | 상세 |
|---------|------|------|
| `seat_reservation` | 좌석 예약 | 2025-12-20 11:00-13:00 KST, RESERVED |
| `meeting_room_reservation` | 회의실 예약 | 2025-12-20 12:00-14:00 KST, 3명, RESERVED |
| `expired_reservation` | 만료된 예약 | 2025-12-18, COMPLETED |
| `canceled_reservation` | 취소된 예약 | 2025-12-21, CANCELED |

### 4.5 시간 Fixture

| Fixture | 설명 | 값 |
|---------|------|-----|
| `mock_now` | 모킹된 현재 시간 | 2025-12-20 19:00 KST (10:00 UTC) |
| `test_date` | 테스트 날짜 | 2025-12-20 |
| `operation_hours` | 운영 시간 | 09:00~22:00 KST |

---

## 5. 통합 테스트 상세

### 5.1 인증 API 테스트 (`test_auth_api.py`)

#### TestLoginAPI

| 테스트 | 요청 | 예상 응답 |
|--------|------|----------|
| `test_login_success_with_valid_student_id` | `POST /api/auth/login` `{"student_id": "202312345"}` | **200**, `is_success: true`, `payload.access_token: "token-202312345-{uuid}"` |
| `test_login_fail_with_blocked_student_id` | `POST /api/auth/login` `{"student_id": "202099999"}` | **400**, `code: "AUTH_INVALID_STUDENT_ID"` |
| `test_login_fail_with_invalid_format` | `POST /api/auth/login` `{"student_id": "12345"}` | **400**, `code: "VALIDATION_ERROR"` |

#### TestAuthenticationRequired

| 테스트 | 요청 | 예상 응답 |
|--------|------|----------|
| `test_access_without_token` | `GET /api/reservations/me` (헤더 없음) | **400**, `code: "AUTH_UNAUTHORIZED"` |
| `test_access_with_invalid_token` | `GET /api/reservations/me` `Authorization: Bearer invalid-token` | **400**, `code: "AUTH_UNAUTHORIZED"` |
| `test_access_with_valid_token` | `GET /api/reservations/me` (유효한 토큰) | **200**, `is_success: true` |

---

### 5.2 좌석 예약 API 테스트 (`test_seat_api.py`)

#### TestCreateSeatReservationAPI

| 테스트 | 요청 | 예상 응답 |
|--------|------|----------|
| `test_create_seat_reservation_success` | `POST /api/reservations/seats` `{"date": "2025-12-21", "start_time": "10:00", "end_time": "12:00", "seat_id": 1}` | **201**, `payload.status: "RESERVED"` |

#### TestRandomSeatReservationAPI

| 테스트 | 요청 | 예상 응답 |
|--------|------|----------|
| `test_random_seat_reservation_success` | `POST /api/reservations/seats/random` (seat_id 생략) | **201**, `payload.seat_id: {할당된 ID}` |
| `test_random_seat_assigned_from_available` | 랜덤 배정 요청 | 배정된 seat_id가 available_seats에 포함 |

#### TestSeatTimeConflictAPI

| 테스트 | 시나리오 | 예상 응답 |
|--------|----------|----------|
| `test_same_seat_same_time_conflict` | 같은 좌석, 같은 시간 두 번째 예약 | **409**, `code: "RESERVATION_CONFLICT"` |
| `test_same_seat_different_time_success` | 같은 좌석, 다른 시간 예약 | **201** |

#### TestSeatDailyLimitAPI

| 테스트 | 시나리오 | 예상 응답 |
|--------|----------|----------|
| `test_daily_limit_exceeded` | 첫 번째 120분 + 두 번째 120분 (총 240분) 후 세 번째 120분 시도 | **400**, `code: "DAILY_LIMIT_EXCEEDED"` |

#### TestSeatOverlapAPI

| 테스트 | 시나리오 | 예상 응답 |
|--------|----------|----------|
| `test_overlap_with_own_seat_reservation` | 같은 시간대 다른 좌석 예약 시도 | **409**, `code: "OVERLAP_WITH_OTHER_FACILITY"` |

#### TestSeatValidationAPI

| 테스트 | 시나리오 | 예상 응답 |
|--------|----------|----------|
| `test_invalid_time_range` | 종료 시간 < 시작 시간 | **400** |
| `test_not_2hour_duration` | 1시간만 예약 (2시간 단위 아님) | **400** |
| `test_outside_operation_hours` | 07:00-09:00 예약 시도 | **400** |
| `test_past_date_reservation` | 과거 날짜 예약 | **400** |

#### TestSeatListAPI

| 테스트 | 요청 | 예상 응답 |
|--------|------|----------|
| `test_get_all_seats` | `GET /seats` | **200**, `payload: [...]` |
| `test_get_single_seat` | `GET /seats/{seat_id}` | **200** |
| `test_get_nonexistent_seat` | `GET /seats/99999` | **400**, `code: "NOT_FOUND"` |

---

### 5.3 회의실 예약 API 테스트 (`test_meeting_room_api.py`)

#### TestCreateMeetingRoomReservationAPI

| 테스트 | 요청 | 예상 응답 |
|--------|------|----------|
| `test_create_meeting_room_reservation_success` | `POST /api/reservations/meeting-rooms` `{"date": "2025-12-21", "start_time": "10:00", "end_time": "11:00", "room_id": 1, "participants": [...]}` | **201**, `payload.status: "RESERVED"` |

#### TestMeetingRoomParticipantValidationAPI

| 테스트 | 시나리오 | 예상 응답 |
|--------|----------|----------|
| `test_minimum_participants_required` | 2명만 참가자 지정 (최소 3명) | **400**, `code: "VALIDATION_ERROR"` |
| `test_three_participants_success` | 정확히 3명 참가자 | **201** |

#### TestMeetingRoomTimeConflictAPI

| 테스트 | 시나리오 | 예상 응답 |
|--------|----------|----------|
| `test_same_room_same_time_conflict` | 같은 회의실, 같은 시간 두 번째 예약 | **409**, `code: "RESERVATION_CONFLICT"` |
| `test_same_room_different_time_success` | 같은 회의실, 다른 시간 | **201** |

#### TestMeetingRoomDailyLimitAPI

| 테스트 | 시나리오 | 예상 응답 |
|--------|----------|----------|
| `test_daily_limit_exceeded` | 60분 + 60분 (총 120분) 후 60분 추가 시도 | **400**, `code: "DAILY_LIMIT_EXCEEDED"` |

#### TestMeetingRoomWeeklyLimitAPI

| 테스트 | 시나리오 | 예상 응답 |
|--------|----------|----------|
| `test_multiple_reservations_in_week` | 같은 주 내 여러 날짜에 예약 | **201** (각각 성공) |

#### TestMeetingRoomParticipantOverlapAPI

| 테스트 | 시나리오 | 예상 응답 |
|--------|----------|----------|
| `test_participant_already_has_reservation` | 참가자가 이미 같은 시간대 다른 예약에 포함 | **409**, `code: "PARTICIPANT_ALREADY_RESERVED"` 또는 `"OVERLAP_WITH_OTHER_FACILITY"` |

#### TestMeetingRoomOverlapWithSeatAPI

| 테스트 | 시나리오 | 예상 응답 |
|--------|----------|----------|
| `test_cannot_reserve_meeting_room_when_has_seat_reservation` | 같은 시간대 좌석 예약이 있을 때 회의실 예약 시도 | **409**, `code: "OVERLAP_WITH_OTHER_FACILITY"` |

#### TestMeetingRoomValidationAPI

| 테스트 | 시나리오 | 예상 응답 |
|--------|----------|----------|
| `test_invalid_time_range` | 종료 시간 < 시작 시간 | **400** |
| `test_not_1hour_duration` | 30분만 예약 (1시간 단위 아님) | **400** |
| `test_outside_operation_hours` | 07:00-08:00 예약 시도 | **400** |
| `test_past_date_reservation` | 과거 날짜 예약 | **400** |

---

### 5.4 예약 관리 API 테스트 (`test_reservation_api.py`)

#### TestGetMyReservationsAPI

| 테스트 | 요청 | 예상 응답 |
|--------|------|----------|
| `test_get_my_reservations_success` | `GET /api/reservations/me` | **200**, `payload.items: [...]` |
| `test_get_my_reservations_empty` | 예약 없을 때 조회 | **200**, `payload.items: []` |
| `test_get_my_reservations_with_date_filter` | `GET /api/reservations/me?from=2025-12-20&to=2025-12-20` | **200**, 필터링된 결과 |
| `test_get_my_reservations_with_type_filter` | `GET /api/reservations/me?type=seat` | **200**, type="seat"인 예약만 |
| `test_get_my_reservations_item_fields` | 조회 결과 필드 검증 | `reservation_id`, `type`, `date`, `start_time`, `end_time`, `status` 포함 |

#### TestCancelReservationAPI

| 테스트 | 요청 | 예상 응답 |
|--------|------|----------|
| `test_cancel_reserved_reservation_success` | `DELETE /api/reservations/me/{id}` | **200**, `payload.status: "CANCELED"` |
| `test_cancel_already_canceled_reservation` | 이미 취소된 예약 재취소 | **400**, `is_success: false` |
| `test_cancel_in_use_reservation` | IN_USE 상태 예약 취소 | **403** |
| `test_cancel_completed_reservation` | COMPLETED 상태 예약 취소 | **403** |
| `test_cancel_other_user_reservation` | 다른 사용자의 예약 취소 | **403** |
| `test_cancel_nonexistent_reservation` | 존재하지 않는 예약 취소 | **400**, `code: "NOT_FOUND"` |
| `test_cancel_without_authentication` | 인증 없이 취소 시도 | **400** |

---

### 5.5 상태 조회 API 테스트 (`test_status_api.py`)

#### TestGetMeetingRoomStatusAPI

| 테스트 | 요청 | 예상 응답 |
|--------|------|----------|
| `test_get_meeting_room_status_success` | `GET /api/status/meeting-rooms?date=2025-12-20` | **200**, `payload: {date, operation_hours, rooms}` |
| `test_get_meeting_room_status_with_reservation` | 예약된 슬롯 조회 | `is_available: false` |
| `test_get_meeting_room_status_without_reservation` | 예약 없는 날짜 | 모든 슬롯 `is_available: true` |
| `test_get_meeting_room_status_canceled_reservation_available` | 취소된 예약 슬롯 | `is_available: true` |

#### TestGetSeatStatusAPI

| 테스트 | 요청 | 예상 응답 |
|--------|------|----------|
| `test_get_seat_status_success` | `GET /api/status/seats?date=2025-12-20` | **200**, `payload: {date, operation_hours, seats}` |
| 슬롯 형식 검증 | - | `{start, end, is_available}` |
| 슬롯 단위 검증 | - | 2시간(120분) 단위 |

#### TestStatusQueryParameters

| 테스트 | 요청 | 예상 응답 |
|--------|------|----------|
| `test_meeting_room_status_without_date_parameter` | `GET /api/status/meeting-rooms` (date 없음) | **400** |
| `test_status_with_invalid_date_format` | `date=20-12-2025` | **400** |
| `test_status_with_valid_date_format` | `date=2025-12-20` | **200** |

---

### 5.6 좌석 예약 상세 테스트 (`test_seat_reservation_api.py`)

#### 실패 예상 케이스 (xfail)

| 테스트 | 시나리오 | 예상 응답 |
|--------|----------|----------|
| `test_reserve_seat_past_date` | 과거 날짜 예약 | **400** |
| `test_reserve_seat_invalid_time_unit` | 30분 단위 예약 | **400** |
| `test_reserve_seat_3_hours_duration` | 3시간 예약 (2시간 단위 아님) | **400** |
| `test_reserve_seat_outside_operating_hours_early` | 07:00-09:00 예약 | **400** |
| `test_reserve_seat_exceeding_daily_limit` | 일일 4시간 초과 | **400** |
| `test_random_seat_no_available_seats` | 모든 좌석 예약됨 | **409** |
| `test_concurrent_seat_reservation_same_seat` | 동시 예약 | 하나는 201, 하나는 409 |
| `test_reserve_nonexistent_seat` | 존재하지 않는 좌석 | **400** 또는 **404** |
| `test_reserve_seat_end_time_before_start_time` | 종료 < 시작 | **400** |
| `test_reserve_seat_same_start_end_time` | 0시간 예약 | **400** |

---

## 6. 단위 테스트 상세

### 6.1 인증 단위 테스트 (`test_auth.py`)

#### TestLoginValidation

| 테스트 | 시나리오 | 예상 결과 |
|--------|----------|----------|
| `test_valid_student_id_login` | 유효한 학번 로그인 | 성공, `last_login_at` 업데이트 |
| `test_invalid_student_id_202099999` | 금지된 학번 | `BusinessException`, `code: AUTH_INVALID_STUDENT_ID` |
| `test_invalid_student_id_202288888` | 금지된 학번 | `BusinessException`, `code: AUTH_INVALID_STUDENT_ID` |
| `test_invalid_student_id_format` | 잘못된 형식 | `ValueError` |
| `test_invalid_student_id_non_numeric` | 숫자가 아닌 학번 | `ValueError` |

#### TestTokenGeneration & TestTokenValidation

| 테스트 | 검증 내용 |
|--------|----------|
| 토큰 형식 | `"token-{student_id}-{uuid}"` |
| 토큰 검증 | `startswith("token-")`, 3개 이상의 하이픈 분할 |

---

### 6.2 회의실 예약 서비스 (`test_meeting_room_service.py`)

#### TestMeetingRoomReservationCreation

| 테스트 | 시나리오 | 예상 결과 |
|--------|----------|----------|
| `test_reserve_meeting_room_success` | 정상 예약 | 성공, `status: RESERVED` |
| `test_reserve_invalid_room_id_fails` | room_id=99 (허용: 1,2,3) | `ValidationError` |

#### TestParticipantValidation

| 테스트 | 시나리오 | 예상 결과 |
|--------|----------|----------|
| `test_min_participants_required` | 2명 < 최소 3명 | `ValueError` |
| `test_duplicate_participants_rejected` | 중복 학번 | `ValueError` |

#### TestMeetingRoomConflictValidation

| 테스트 | 시나리오 | 예상 결과 |
|--------|----------|----------|
| `test_same_room_same_time_conflict` | 같은 회의실, 같은 시간 | `ConflictException`, `code: RESERVATION_CONFLICT` |
| `test_same_room_different_time_no_conflict` | 같은 회의실, 다른 시간 | 성공 |

#### TestMeetingRoomDailyLimitValidation

| 테스트 | 시나리오 | 예상 결과 |
|--------|----------|----------|
| `test_daily_limit_exceeded` | 120분 초과 | `LimitExceededException`, `code: DAILY_LIMIT_EXCEEDED` |
| `test_within_daily_limit` | 120분 이내 | 성공 |

#### TestMeetingRoomWeeklyLimitValidation

| 테스트 | 시나리오 | 예상 결과 |
|--------|----------|----------|
| `test_weekly_limit_exceeded` | 5일간 60분씩 (총 300분) 후 추가 예약 | `LimitExceededException`, `code: WEEKLY_LIMIT_EXCEEDED` |
| `test_participant_weekly_limit_exceeded` | 참가자 주간 한도 초과 | `LimitExceededException` |

---

### 6.3 좌석 예약 서비스 (`test_seat_service.py`)

#### TestSeatQuery

| 테스트 | 검증 내용 |
|--------|----------|
| `test_get_seat_by_id` | 좌석 조회 성공 |
| `test_get_nonexistent_seat` | 없는 좌석 → `None` 반환 |
| `test_get_all_seats` | 전체 좌석 목록 반환 |
| `test_get_seats_count` | 좌석 개수 반환 |

#### TestSeatReservationCreation

| 테스트 | 시나리오 | 예상 결과 |
|--------|----------|----------|
| `test_reserve_seat_with_specific_seat_id` | 특정 좌석 예약 | 성공, `status: RESERVED` |
| `test_reserve_seat_random_assignment` | seat_id=None | 랜덤 배정 성공 |
| `test_reserve_unavailable_seat_fails` | 이용 불가 좌석 | `BusinessException`, `code: SEAT_NOT_AVAILABLE` |

#### TestSeatTimeConflict

| 테스트 | 시나리오 | 예상 결과 |
|--------|----------|----------|
| `test_same_seat_same_time_conflict` | 같은 좌석, 같은 시간 | `ConflictException`, `code: RESERVATION_CONFLICT` |
| `test_same_seat_different_time_no_conflict` | 같은 좌석, 다른 시간 | 성공 |

#### TestSeatDailyLimitValidation

| 테스트 | 시나리오 | 예상 결과 |
|--------|----------|----------|
| `test_daily_limit_exceeded_with_existing_reservations` | 240분 초과 | `LimitExceededException`, `code: DAILY_LIMIT_EXCEEDED` |
| `test_within_daily_limit_single_reservation` | 120분 | 성공 |

#### TestRandomSeatAssignment

| 테스트 | 시나리오 | 예상 결과 |
|--------|----------|----------|
| `test_random_assignment_when_seats_available` | 가용 좌석 있음 | seat_id 할당 |
| `test_random_assignment_avoids_occupied_seats` | 일부 좌석 점유 | 점유된 좌석 제외하고 배정 |
| `test_random_assignment_fails_when_all_occupied` | 모든 좌석 점유 | `ConflictException`, `code: RESERVATION_CONFLICT` |

---

### 6.4 예약 서비스 (`test_reservation_service.py`)

#### TestReservationQuery

| 테스트 | 검증 내용 |
|--------|----------|
| `test_get_user_reservations` | 사용자 예약 목록 조회 |
| `test_get_user_reservations_filtered_by_date` | 날짜별 필터링 |
| `test_get_user_reservations_filtered_by_type` | seat/meeting_room 타입 필터링 |
| `test_get_empty_reservations` | 예약 없으면 빈 리스트 |

#### TestReservationCancellation

| 테스트 | 시나리오 | 예상 결과 |
|--------|----------|----------|
| `test_cancel_reserved_reservation` | RESERVED 상태 취소 | `status: CANCELED` |
| `test_cancel_already_canceled_reservation` | 이미 취소됨 | `BusinessException`, `code: RESERVATION_ALREADY_CANCELED` |
| `test_cancel_in_use_reservation` | IN_USE 상태 취소 | `ForbiddenException`, `code: AUTH_FORBIDDEN` |
| `test_cancel_completed_reservation` | COMPLETED 상태 취소 | `ForbiddenException` |
| `test_cancel_other_user_reservation` | 다른 사용자 예약 | `ForbiddenException` |
| `test_cancel_nonexistent_reservation` | 없는 예약 | `BusinessException`, `code: NOT_FOUND` |

#### TestReservationStateTransition

| 상태 전이 | 허용 여부 |
|----------|----------|
| RESERVED → IN_USE | ✅ 허용 |
| IN_USE → COMPLETED | ✅ 허용 |
| RESERVED → CANCELED | ✅ 허용 |
| CANCELED → RESERVED | ❌ 불허 |
| COMPLETED → IN_USE | ❌ 불허 |

---

### 6.5 예약 검증 (`test_reservation_validation.py`)

#### TestReservationTimeValidation (xfail)

| 테스트 | 검증 내용 |
|--------|----------|
| `validate_future_date_only` | 과거 날짜 검증 |
| `validate_2_hour_intervals_only` | 2시간 단위 검증 |
| `validate_operating_hours` | 09:00-22:00 운영 시간 검증 |

#### TestOverlapDetection

| 테스트 | 시나리오 | 예상 결과 |
|--------|----------|----------|
| `test_overlap_detection_boundary_case_same_end_start` | 종료 = 시작 | 겹침 없음 |
| `test_overlap_detection_one_minute_overlap` | 1분 겹침 | 충돌 감지 |

#### TestParticipantValidation

| 테스트 | 검증 내용 |
|--------|----------|
| `validate_participant_count_boundary` | 최소 3명 검증 |
| `validate_no_duplicate_participants` | 중복 참가자 검증 |
| `validate_owner_not_in_participants` | 예약자는 참가자 목록 제외 |

---

### 6.6 상태 조회 서비스 (`test_status_service.py`)

#### TestMeetingRoomStatusQuery

| 테스트 | 검증 내용 |
|--------|----------|
| `test_get_meeting_room_status_all_available` | 전체 가용 |
| `test_get_meeting_room_status_partial_reserved` | 일부 예약됨 |
| `test_get_meeting_room_status_all_reserved` | 전체 예약됨 |
| `test_meeting_room_status_slot_unit` | 60분 단위 |
| `test_meeting_room_status_operation_hours` | 09:00-22:00 |

#### TestSeatStatusQuery

| 테스트 | 검증 내용 |
|--------|----------|
| `test_get_seat_status_all_available` | 전체 가용 |
| `test_get_seat_status_partial_reserved` | 일부 예약됨 |
| `test_get_seat_status_all_reserved` | 전체 예약됨 |
| `test_seat_status_slot_unit` | 120분 단위 |
| `test_seat_status_recommended_slots` | 6-7개 슬롯 |

#### TestAvailableSlotCalculation

| 테스트 | 시나리오 | 예상 결과 |
|--------|----------|----------|
| `test_calculate_available_slots_no_reservation` | 예약 없음 | 모든 슬롯 가용 |
| `test_calculate_available_slots_with_reservation` | 예약 있음 | 해당 시간 제외 |
| `test_canceled_reservation_makes_slot_available` | 취소된 예약 | 슬롯 복구 |

---

## 7. 비즈니스 규칙 검증 요약

### 7.1 예약 시간 규칙

| 항목 | 좌석 예약 | 회의실 예약 |
|------|----------|------------|
| **시간 단위** | 2시간 단위만 허용 | 1시간 단위만 허용 |
| **일일 한도** | 240분 (4시간) | 120분 (2시간) |
| **주간 한도** | 없음 | 300분 (5시간, 월~일) |
| **운영 시간** | 09:00-22:00 KST | 09:00-22:00 KST |
| **과거 날짜** | 불허 | 불허 |

### 7.2 회의실 참가자 규칙

| 항목 | 규칙 |
|------|------|
| 최소 인원 | 3명 |
| 최대 인원 | 제한 없음 |
| 중복 학번 | 불허 |
| 예약자 포함 | 참가자 목록에서 제외 |

### 7.3 시설 중복 예약 규칙

| 시나리오 | 허용 여부 |
|----------|----------|
| 같은 시간대 좌석 여러 개 | ❌ 불가 |
| 같은 시간대 좌석 + 회의실 | ❌ 불가 |
| 같은 좌석/회의실 다른 사용자 | ❌ 불가 (409 Conflict) |

### 7.4 예약 상태 전이

```
정상 흐름:
  RESERVED → IN_USE → COMPLETED
  RESERVED → CANCELED

취소 불가 상태:
  IN_USE, COMPLETED, CANCELED
```

---

## 8. 테스트 환경 설정

### 8.1 테스팅 라이브러리

**backend/requirements-test.txt**

```
pytest==7.4.3              # 테스트 프레임워크
pytest-cov==4.1.0          # 코드 커버리지 측정
pytest-asyncio==0.21.1     # 비동기 테스트 지원
pytest-mock==3.12.0        # Mock 객체 지원
httpx==0.25.2              # TestClient용 HTTP 클라이언트
faker==20.1.0              # 테스트 데이터 생성
```

### 8.2 pytest 설정 파일

**backend/pytest.ini**

```ini
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
    status: 상태 조회 관련 테스트
    slow: 느린 테스트
```

### 8.3 테스트 실행 명령어

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

---

## 9. 테스트 구현 현황

### 9.1 단위 테스트

| 파일 | 테스트 클래스 | 테스트 수 |
|------|--------------|----------|
| `test_auth.py` | TestLoginValidation, TestTokenGeneration, TestTokenValidation | 11개 |
| `test_seat_service.py` | TestSeatQuery, TestSeatReservationCreation, TestRandomSeatAssignment, ... | 15개+ |
| `test_meeting_room_service.py` | TestMeetingRoomReservationCreation, TestParticipantValidation, ... | 15개+ |
| `test_reservation_service.py` | TestReservationQuery, TestReservationCancellation, TestReservationStateTransition, ... | 23개 |
| `test_reservation_validation.py` | TestReservationTimeValidation, TestOverlapDetection, TestParticipantValidation | 10개+ |
| `test_status_service.py` | TestMeetingRoomStatusQuery, TestSeatStatusQuery, TestAvailableSlotCalculation | 16개 |

### 9.2 통합 테스트

| 파일 | 테스트 클래스 | 테스트 수 |
|------|--------------|----------|
| `test_auth_api.py` | TestLoginAPI, TestAuthenticationRequired | 6개+ |
| `test_seat_api.py` | TestCreateSeatReservationAPI, TestRandomSeatReservationAPI, TestSeatTimeConflictAPI, ... | 13개+ |
| `test_seat_reservation_api.py` | 상세 좌석 예약 테스트 (xfail 포함) | 10개+ |
| `test_meeting_room_api.py` | TestCreateMeetingRoomReservationAPI, TestMeetingRoomParticipantValidationAPI, ... | 15개+ |
| `test_reservation_api.py` | TestGetMyReservationsAPI, TestCancelReservationAPI | 12개+ |
| `test_status_api.py` | TestGetMeetingRoomStatusAPI, TestGetSeatStatusAPI, TestStatusQueryParameters | 10개+ |

### 9.3 구현 상태

| 항목 | 상태 |
|------|------|
| conftest.py | ✅ 완료 (13개 fixture) |
| utils/ | ✅ 완료 (assertions, factories, helpers) |
| unit/ | ✅ 완료 |
| integration/ | ✅ 완료 |

---

## 10. 코드 커버리지 목표

| 계층 | 목표 커버리지 |
|------|--------------|
| Service 계층 | 100% |
| API 계층 | 90% 이상 |
| 전체 | 80% 이상 |
