# 💾 프런트엔드 데이터 저장 구조

프런트엔드는 별도의 DB를 사용하지 않으며, **`sessionStorage`와 메모리 상태**로 데이터를 관리합니다.

---

## 1. sessionStorage 키 목록

| Key | 타입 | 설명 |
| --- | --- | --- |
| `studentId` | string | 로그인한 학번 |
| `accessToken` | string | 백엔드 인증 토큰 |
| `pendingReservation` | JSON string | 예약 진행 상태 (페이지 간 전달용) |

---

## 2. `pendingReservation` 구조

예약 가능 시간에서 선택한 정보를 다음 페이지로 넘길 때 사용합니다.

```json
{
  "type": "MEETING",
  "date": "2030-01-08",
  "slot": {
    "id": "9-10",
    "label": "09:00 ~ 10:00",
    "startMinutes": 540,
    "endMinutes": 600,
    "start": "09:00",
    "end": "10:00"
  }
}
```

**호환 필드**
- 이전 버전 데이터는 `slotId` 또는 `slotIds`만 포함될 수 있습니다.  
  `frontend/js/app.js`의 `normalizePendingReservation()`가 이를 복구합니다.

---

## 3. 런타임 상태 (`frontend/js/app.js`)

`state` 객체는 브라우저 메모리에만 존재하며 새로고침 시 초기화됩니다.

```js
const state = {
  studentId: null,
  filters: { spaceType: null, date: "" },
  meetingStatus: null,
  seatStatus: null,
  selectedReadingSlot: null,
  selectedSeat: null,
  selectedMeetingRoom: null,
  participants: ["", "", ""],
};
```

---

## 4. 저장/갱신 시점

- **로그인 성공 시**
  - `studentId`, `accessToken` 저장
- **예약 조건 선택 시**
  - `pendingReservation` 저장
- **예약 성공 시**
  - `pendingReservation` 제거

