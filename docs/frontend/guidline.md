# 📝 프런트엔드 개발 가이드라인 (Convention)

정적 HTML 기반 구조이므로 **DOM 구조와 JS 로직의 일관성**이 가장 중요합니다.  
아래 규칙은 현 프로젝트의 코드 스타일과 동작 방식을 기준으로 작성되었습니다.

---

## 1. 역할 분리 (Separation of Concerns)

- **HTML**: 마크업 구조와 접근성(aria/label)을 담당합니다.
- **JS**: 이벤트 바인딩, 상태 관리, API 호출만 담당합니다.
- **CSS**: 재사용 가능한 클래스(`notice`, `error`, `success`, `hidden`)로 상태를 표현합니다.

**✅ 권장**
- 공통 로직은 `frontend/js/app.js`에 집중
- 페이지 특화 로직은 필요 시 별도 파일로 분리

**❌ 비권장**
- HTML 내부에 긴 비즈니스 로직 포함
- DOM 구조에 의존하는 하드코딩된 셀렉터 남발

---

## 2. DOM 접근 규칙

- `document.getElementById()` 결과는 **반드시 null 체크** 후 사용합니다.
- UI 변경은 `textContent`, `classList.toggle()` 중심으로 처리합니다.
- 상태 메시지는 `p.notice`, `p.error`, `p.success`로 통일합니다.

---

## 3. 상태 관리 원칙

`frontend/js/app.js`의 `state` 객체를 중심으로 관리합니다.

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

새 상태를 추가할 때는:
1. 초기값 정의
2. 페이지 전환 시 초기화 위치 확인
3. DOM 렌더링 함수에서 반영

---

## 4. 호출 규칙

- 직접 `fetch()`를 호출하지 말고 `ApiClient`를 사용합니다.
- 예외는 `try/catch`로 감싸고, 메시지는 사용자에게 표시합니다.
- `payload` 외의 원본 응답을 UI에 사용하지 않습니다.

```js
try {
  const payload = await ApiClient.fetchSeatStatus(date);
  state.seatStatus = payload;
} catch (error) {
  showError(error.message);
}
```

---

## 5. 세션 키 규칙

| 키 | 의미 | 저장 위치 |
| --- | --- | --- |
| `studentId` | 로그인 학번 | `sessionStorage` |
| `accessToken` | API 인증 토큰 | `sessionStorage` |
| `pendingReservation` | 예약 진행 상태 | `sessionStorage` |

키 이름 변경 시 `app.js`, `login.html`, `my-reservations.html`을 함께 수정해야 합니다.

---

## 6. 날짜/시간 처리

- 날짜 비교는 `parseDateOnly`, `isPastDate` 유틸을 사용합니다.
- 오늘 날짜의 경우 **현재 시간 이전 슬롯은 숨기거나 비활성화**합니다.
- 예약 가능 시간만 UI에 보여주는 것이 기본 정책입니다.

---

## 7. 테스트 연계 규칙

- 순수 로직(`reservation-engine.js`, `api-client.js`)은 Jest로 테스트합니다.
- UI 로직은 작은 함수로 쪼개 테스트 가능한 형태로 유지합니다.
- 새로운 정책 추가 시 테스트도 함께 업데이트합니다.
