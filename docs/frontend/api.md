# 🌐 프런트엔드 API 사용 문서

이 문서는 **프런트에서 어떤 호출을 어디서 하는지**에 초점을 둡니다.  
통신 로직은 `frontend/js/api-client.js`에 집중되어 있습니다.

---

## 0. 기본 설정

### 0.1 Base URL

- 기본값: `http://127.0.0.1:8000`
- 전역 변수 `APP_API_BASE_URL`이 있으면 해당 값을 사용합니다.

```js
const API_BASE_URL = global.APP_API_BASE_URL || "http://127.0.0.1:8000";
```

### 0.2 인증 토큰 처리

- 로그인 성공 시 `accessToken`을 `sessionStorage`에 저장
- `ApiClient`는 `Authorization: Bearer <token>` 헤더를 자동으로 붙입니다

---

## 1) 인증 호출

### 1.1 로그인

**POST** `/api/auth/login`

**Request**
```json
{
  "student_id": "202300001"
}
```

**Response (payload)**
```json
{
  "student_id": 202300001,
  "access_token": "token-..."
}
```

**어디서 호출하나**
- `frontend/login.html` inline script

**요약**
- `student_id`만 전송하고 응답에서 `studentId`, `accessToken`을 저장합니다.

---

## 2) 예약 현황 조회 호출

### 2.1 회의실 현황

**GET** `/api/status/meeting-rooms?date=YYYY-MM-DD`

**Response (payload)**
```json
{
  "date": "2030-01-08",
  "operation_hours": { "start": "09:00", "end": "18:00" },
  "slot_unit_minutes": 60,
  "rooms": [
    {
      "room_id": 1,
      "slots": [
        { "start": "09:00", "end": "10:00", "is_available": true }
      ]
    }
  ]
}
```

### 2.2 좌석 현황

**GET** `/api/status/seats?date=YYYY-MM-DD`

**Response (payload)**
```json
{
  "date": "2030-01-08",
  "operation_hours": { "start": "09:00", "end": "18:00" },
  "slot_unit_minutes": 120,
  "seats": [
    {
      "seat_id": 1,
      "slots": [
        { "start": "09:00", "end": "11:00", "is_available": true }
      ]
    }
  ]
}
```

---

## 3) 예약 생성 호출

### 3.1 회의실 예약 생성

**POST** `/api/reservations/meeting-rooms`

**Request**
```json
{
  "room_id": 1,
  "date": "2030-01-08",
  "start_time": "09:00",
  "end_time": "10:00",
  "participants": [
    { "student_id": "202300001" },
    { "student_id": "202300002" },
    { "student_id": "202300003" }
  ]
}
```

### 3.2 좌석 예약 생성

**POST** `/api/reservations/seats`

**Request**
```json
{
  "date": "2030-01-08",
  "start_time": "09:00",
  "end_time": "11:00",
  "seat_id": 12
}
```

### 3.3 랜덤 좌석 예약

**POST** `/api/reservations/seats/random`

**Request**
```json
{
  "date": "2030-01-08",
  "start_time": "09:00",
  "end_time": "11:00"
}
```

---

## 4) 내 예약 조회/취소 호출

### 4.1 내 예약 목록 조회

**GET** `/api/reservations/me?from=YYYY-MM-DD&to=YYYY-MM-DD&type=meeting_room|seat`

### 4.2 예약 취소

**DELETE** `/api/reservations/me/{reservation_id}`

---

## 5) 에러 처리 규칙

`ApiClient`는 다음 조건에서 `ApiError`를 throw 합니다.

- HTTP 상태 코드가 2xx가 아닌 경우
- 응답 본문에 `is_success === false`인 경우

필드:
- `message`: 사용자에게 보여줄 메시지
- `status`: HTTP 상태 코드
- `code`: 백엔드 에러 코드
- `payload`: 원본 payload

---

## 6) 호출 위치 요약

| 호출 | 위치 | 사용 목적 |
| --- | --- | --- |
| `POST /api/auth/login` | `frontend/login.html` | 로그인 |
| `GET /api/status/meeting-rooms` | `frontend/js/app.js` | 회의실 시간대 표시 |
| `GET /api/status/seats` | `frontend/js/app.js` | 좌석 시간대 표시/좌석 지도 |
| `POST /api/reservations/meeting-rooms` | `frontend/js/app.js` | 회의실 예약 생성 |
| `POST /api/reservations/seats` | `frontend/js/app.js` | 좌석 예약 생성 |
| `POST /api/reservations/seats/random` | `frontend/js/app.js` | 랜덤 좌석 예약 |
| `GET /api/reservations/me` | `frontend/my-reservations.html` | 내 예약 조회 |
| `DELETE /api/reservations/me/{reservation_id}` | `frontend/my-reservations.html` | 예약 취소 |
