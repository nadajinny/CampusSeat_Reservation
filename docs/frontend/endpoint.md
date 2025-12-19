# 📄 프런트엔드 페이지/화면 문서

정적 HTML 페이지별로 **어디서 호출하고 어떻게 쓰는지**를 중심으로 정리합니다.

---

## 1) `index.html`

- **역할**: `login.html`로 자동 리다이렉트
- **스크립트**: inline redirect

---

## 2) `login.html`

- **역할**: 로그인 및 토큰 저장
- **호출**: `POST /api/auth/login`
- **스크립트**: inline script

**주요 DOM 요소**
- `#login-form`
- `#studentId`
- `#password`
- `#login-status`

---

## 3) `dashboard.html`

- **역할**: 기능 선택 메뉴 + 로그아웃
- **스크립트**: `frontend/js/app.js`
  - `bindLogout()`로 세션 제거

**주요 DOM 요소**
- `#studentIdText`
- `#logoutBtn`

---

## 4) `search-availability.html`

- **역할**: 시설 유형/날짜 선택 → 예약 가능 시간 표시
- **스크립트**: `frontend/js/app.js`
- **호출**:
  - `GET /api/status/meeting-rooms`
  - `GET /api/status/seats`

**주요 DOM 요소**
- `#reservationDate`
- `#reservationDateMessage`
- `input[name="spaceType"]`
- `#meeting-time-list`
- `#reading-time-grid`
- `#readingProceedBtn`

**특이사항**
- 과거 날짜는 선택 즉시 안내 메시지 표시
- 오늘 날짜는 지나간 시간 슬롯 숨김 처리

---

## 5) `meeting-room-reservation.html`

- **역할**: 회의실 선택 및 예약 생성
- **스크립트**: `frontend/js/app.js`
- **호출**: `POST /api/reservations/meeting-rooms`

**주요 DOM 요소**
- `#meeting-room-page`
- `#meeting-context-date`
- `#meeting-context-slot`
- `#meeting-room-list`
- `#meeting-summary`
- `#meeting-context-error`

---

## 6) `seat-reservation.html`

- **역할**: 좌석 선택/랜덤 배정 및 예약 생성
- **스크립트**: `frontend/js/app.js`
- **호출**:
  - `GET /api/status/seats`
  - `POST /api/reservations/seats`
  - `POST /api/reservations/seats/random`

**주요 DOM 요소**
- `#seat-reservation-page`
- `#reading-context-slots`
- `#reading-seat-map`
- `#randomSeatBtn`
- `#reading-summary`
- `#reading-context-error`

---

## 7) `my-reservations.html`

- **역할**: 내 예약 목록 조회 및 취소
- **스크립트**: inline script
- **호출**:
  - `GET /api/reservations/me`
  - `DELETE /api/reservations/me/{reservation_id}`

**주요 DOM 요소**
- `#filter-form`
- `#filterFrom`
- `#filterTo`
- `#filterType`
- `#reservationList`
- `#reservation-status`
- `#reservation-empty`
