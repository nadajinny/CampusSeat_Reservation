### 공통 응답 포맷

```json
{
  "is_success": true,
  "code": null,
  "payload": {}
}
```

- 성공: `is_success=true`, `code=null`, `payload`에 결과
- 실패: `is_success=false`, `code`에 에러 코드 문자열, `payload`에는 상세(메시지/필드오류 등)

### 공통 에러 코드(권장)

- `AUTH_INVALID_STUDENT_ID` (학번이 202099999 또는 202288888)
- `AUTH_UNAUTHORIZED` (토큰/세션 없음 또는 만료)
- `VALIDATION_ERROR` (필수값 누락/포맷 오류)
- `TIME_OUT_OF_OPERATION_HOURS`
- `RESERVATION_CONFLICT` (해당 시설/좌석이 이미 예약됨)
- `OVERLAP_WITH_OTHER_FACILITY` (동일 시간대 타 시설 예약 존재)
- `DAILY_LIMIT_EXCEEDED` (좌석 1일 4시간, 회의실 1일 2시간)
- `WEEKLY_LIMIT_EXCEEDED` (회의실 1주 5시간)
- `PARTICIPANT_MIN_NOT_MET` (회의실 참여자 3명 미만)
- `NOT_FOUND`
- `FORBIDDEN` (내 예약 아님, 또는 시작 후 취소 시도)

## 0.1 운영 시간

- 운영시간: **09:00 ~ 18:00**
- 회의실: **1시간 단위 슬롯**
- 좌석: **2시간 단위 슬롯**
    - 권장 슬롯: **09-11, 10-12, 11-13, 12-14, 13-15, 14-16, 15-17, 16-18**
    - (총 8개 슬롯, 운영시간 내 2시간 단위로 예약 가능)

## 0.2 시간 제한

- 회의실(예약자 기준)
    - **일일 최대 2시간**
    - **주간 최대 5시간**
- 좌석(예약자 기준)
    - **일일 최대 4시간**
    - (슬롯 2개까지 선택 가능: 2시간×2)

## 0.3 중복/겹침 금지

- 같은 회의실(room_id): 동일 시간대 중복 예약 불가
- 같은 좌석(seat_id): 동일 시간대 중복 예약 불가
- **동일 시간대에 타 시설(회의실↔좌석) 예약 동시 보유 불가** (예약자 기준)

## 0.4 회의실 참여자 규칙

- 회의실 예약은 **참여자 명단 최소 3명**

---

## 1) 인증 API (하드코딩) — 필수 구현 범위

### 1.1 로그인(허재민)(개발완료)

**POST** `/api/auth/login`

**Request**

```json
{
  "student_id": "202312345"
}

```

**Success 200**

```json
{
  "is_success": true,
  "code": null,
  "payload": {
    "access_token": "token-string",
    "student_id": 202312345
  }
}

```

**Fail 401 (잘못된 학번 2개)**

```json
{
  "is_success": false,
  "code": "AUTH_INVALID_STUDENT_ID",
  "payload": {
    "message": "유효하지 않은 학번입니다."
  }
}

```

**검증 규칙**

- 입력이 9자리 정수 문자열/정수인지 확인(아니면 `VALIDATION_ERROR`)
- 값이 `202099999` 또는 `202288888`이면 실패
- 그 외 9자리 정수는 성공 처리

---

## 2) "현재 예약 현황 조회"(b) API (허재민)(개발중)

### 2.1 날짜별 회의실 예약 현황 조회

**GET** `/api/status/meeting-rooms`

**Query**

- `date` (필수) `YYYY-MM-DD`

**Success 200**

```json
{
  "is_success": true,
  "code": null,
  "payload": {
    "date": "2025-12-20",
    "operation_hours": { "start": "09:00", "end": "18:00" },
    "slot_unit_minutes": 60,
    "rooms": [
      {
        "room_id": 1,
        "slots": [
          { "start": "09:00", "end": "10:00", "is_available": true },
          { "start": "10:00", "end": "11:00", "is_available": false }
        ]
      },
      { "room_id": 2, "slots": [] },
      { "room_id": 3, "slots": [] }
    ]
  }
}
```

### 2.2 날짜별 좌석 예약 현황 조회

**GET** `/api/status/seats`

**Query**

- `date` (필수) `YYYY-MM-DD`

**Success 200**

```json
{
  "is_success": true,
  "code": null,
  "payload": {
    "date": "2025-12-20",
    "operation_hours": { "start": "09:00", "end": "18:00" },
    "slot_unit_minutes": 120,
    "seats": [
      {
        "seat_id": 1,
        "slots": [
          { "start": "09:00", "end": "11:00", "is_available": true },
          { "start": "10:00", "end": "12:00", "is_available": true },
          { "start": "11:00", "end": "13:00", "is_available": false },
          { "start": "12:00", "end": "14:00", "is_available": true },
          { "start": "13:00", "end": "15:00", "is_available": true },
          { "start": "14:00", "end": "16:00", "is_available": true },
          { "start": "15:00", "end": "17:00", "is_available": false },
          { "start": "16:00", "end": "18:00", "is_available": true }
        ]
      }
    ]
  }
}
```

---

## 3) “예약 수행”(a) API

### 3.1 회의실 예약 생성(황지찬)(개발중)

**POST** `/api/reservations/meeting-rooms`

**Request**

```json
{
  "room_id": 1,
  "date": "2025-12-20",
  "start_time": "10:00",
  "end_time": "11:00",
  "participants": [
    { "student_id": "202312345", "name": "홍길동" },
    { "student_id": "202312346", "name": "김철수" },
    { "student_id": "202312347", "name": "이영희" }
  ]
}

```

**Success 201**

```json
{
  "is_success": true,
  "code": null,
  "payload": {
    "reservation_id": 1001,
    "type": "meeting_room",
    "room_id": 1,
    "date": "2025-12-20",
    "start_time": "10:00",
    "end_time": "11:00",
    "status": "RESERVED"
  }
}

```

### Fail 예시

- 참여자 미달

```json
{
  "is_success": false,
  "code": "PARTICIPANT_MIN_NOT_MET",
  "payload": { "message": "최소 3명 이상 입력해야 합니다." }
}

```

**검증**

- 운영시간/1시간 단위
- 해당 회의실 동일 시간대 중복 금지 → `RESERVATION_CONFLICT`
- participants 길이 ≥ 3 → 아니면 `PARTICIPANT_MIN_NOT_MET`
- 예약자(로그인 student_id)의 회의실 일 2시간 초과 금지 → `DAILY_LIMIT_EXCEEDED`
- 회의실 주 5시간 초과 금지 → `WEEKLY_LIMIT_EXCEEDED`
- 동일 시간대에 좌석 예약(본인) 존재 금지 → `OVERLAP_WITH_OTHER_FACILITY`

### 3.2 좌석 예약 생성 (직접 선택)

**POST** `/api/reservations/seats`

**Request**

```json
{
  "date": "2025-12-20",
  "start_time": "09:00",
  "end_time": "11:00",
  "seat_id": 12
}

```

**Success 201**

```json
{
  "is_success": true,
  "code": null,
  "payload": {
    "reservation_id": 2001,
    "type": "seat",
    "seat_id": 12,
    "date": "2025-12-20",
    "start_time": "09:00",
    "end_time": "11:00",
    "status": "RESERVED"
  }
}

```

**검증**

- 운영시간/2시간 단위
- 해당 좌석 동일 시간대 중복 금지 → `RESERVATION_CONFLICT`
- 본인 좌석 1일 4시간 초과 금지 → `DAILY_LIMIT_EXCEEDED`
- 동일 시간대 회의실 예약(본인) 존재 금지 → `OVERLAP_WITH_OTHER_FACILITY`

### 3.3 좌석 예약 생성 (랜덤 배정)

**POST** `/api/reservations/seats/random`

**Request**

```json
{
  "date": "2025-12-20",
  "start_time": "09:00",
  "end_time": "11:00"
}

```

**Success 201**

```json
{
  "is_success": true,
  "code": null,
  "payload": {
    "reservation_id": 2002,
    "type": "seat",
    "seat_id": 37,
    "date": "2025-12-20",
    "start_time": "09:00",
    "end_time": "11:00",
    "status": "RESERVED"
  }
}

```

**Fail 409 (가용 좌석 없음)**

```json
{
  "is_success": false,
  "code": "RESERVATION_CONFLICT",
  "payload": { "message": "해당 시간대에 예약 가능한 좌석이 없습니다." }
}

```

---

## 4) “본인의 예약내역 확인”(c) API

### 4.1 내 예약 목록 조회 (회의실+좌석 통합)

**GET** `/api/reservations/me`

**Query (선택)**

- `from` = `YYYY-MM-DD`
- `to` = `YYYY-MM-DD`
- `type` = `meeting_room` | `seat`

**Success 200**

```json
{
  "is_success": true,
  "code": null,
  "payload": {
    "items": [
      {
        "reservation_id": 1001,
        "type": "meeting_room",
        "room_id": 1,
        "date": "2025-12-20",
        "start_time": "10:00",
        "end_time": "11:00",
        "status": "RESERVED"
      },
      {
        "reservation_id": 2001,
        "type": "seat",
        "seat_id": 12,
        "date": "2025-12-21",
        "start_time": "09:00",
        "end_time": "11:00",
        "status": "RESERVED"
      }
    ]
  }
}

```

### 4.2 내 예약 취소(선택 구현 권장)

요구사항에 “취소”가 명시되진 않았지만, SRS에는 포함되어 있어 팀 구현 여력 있으면 넣는 게 자연스럽습니다.

**DELETE** `/api/reservations/me/1`

**Success 200**

```json
// 응답: 200 OK
{
  "is_success": true,
  "code": null,
  "payload": {
    "reservation_id": 1,
    "type": "meeting_room",
    "room_id": 1,
    "seat_id": null,
    "status": "CANCELED"
  }
}

```

또는 좌석 예약 취소 시:

```json
// 응답: 200 OK
{
  "is_success": true,
  "code": null,
  "payload": {
    "reservation_id": 2,
    "type": "seat",
    "room_id": null,
    "seat_id": 12,
    "status": "CANCELED"
  }
}

```

**Fail 400 이미 취소된 예약**

시나리오 4: 중복 취소 시도 → 실패 ❌
// 예약 상태: CANCELED (이미 취소됨)
**DELETE** ```/api/reservations/me/1```
```json
// 응답: 400 BAD_REQUEST
{
  "is_success": false,
  "code": "RESERVATION_ALREADY_CANCELED",
  "payload": {
    "message": "이미 취소된 예약입니다."
  }
}
```

**Fail 403 (시작 후 취소 불가 / 내 예약 아님)**

시나리오 2: IN_USE 상태 → 취소 실패 ❌
// 예약 상태: IN_USE (사용 중)
**DELETE** `/api/reservations/me/2`
```json

// 응답: 403 FORBIDDEN
{
  "is_success": false,
  "code": "AUTH_FORBIDDEN",
  "payload": {
    "message": "사용 중인 예약은 취소할 수 없습니다."
  }
}
```
시나리오 3: COMPLETED 상태 → 취소 실패 ❌
// 예약 상태: COMPLETED (완료됨)
**DELETE** ```/api/reservations/me/3```
```json
// 응답: 403 FORBIDDEN
{
  "is_success": false,
  "code": "AUTH_FORBIDDEN",
  "payload": {
    "message": "완료된 예약은 취소할 수 없습니다."
  }
}

```

---

## 5) (선택) 시설 메타 조회 API

프론트가 고정값(회의실 1~3, 좌석 1~70)을 하드코딩해도 되지만, 백엔드에서 내려주면 확장/유지보수에 유리합니다.

- **GET** `/api/facilities`