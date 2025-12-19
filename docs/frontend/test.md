# ✅ 프런트엔드 테스트 문서

프런트엔드는 **DOM 의존성이 없는 순수 로직**을 `frontend/js/`에 두고 Jest로 단위 테스트합니다.  
이 문서는 **어디를 어떻게 테스트하고 있는지**, **테스트를 확장하는 방법**을 정리합니다.

---

## 1. 테스트 목적

- 예약 정책/시간 계산 로직의 회귀 방지
- API 호출 규칙(헤더/경로/에러 처리) 검증
- UI 로직을 순수 함수로 분리하기 위한 기준 제공

---

## 2. 테스트 위치

```
frontend/__tests__/
├── reservation-engine.test.js
└── api-client.test.js
```

---

## 3. 실행 방법

```bash
cd frontend
npm install
npm test
```

### 빠른 실행 예시

```bash
# 특정 파일만 실행
npx jest reservation-engine.test.js

# 감시 모드
npx jest api-client.test.js --watch
```

---

## 4. 테스트 범위 상세

### 4.1 ReservationEngine

**대상 파일**
- `frontend/js/reservation-engine.js`

**검증 포인트**
- 회의실 예약 규칙(인증/과거 날짜/참여자 조건/중복/일일·주간 한도)
- 좌석 예약 규칙(슬롯 선택/운영시간/좌석 중복/일일 한도)
- 유틸리티 함수
  - 슬롯 겹침 판정
  - 주간 범위 계산
  - 날짜 파싱 및 과거 판정

**테스트 스타일**
- 실패 케이스 우선 → 성공 케이스 순
- 정책 변경 시 메시지까지 함께 업데이트

---

### 4.2 ApiClient

**대상 파일**
- `frontend/js/api-client.js`

**검증 포인트**
- 인증 정보 저장/삭제 (`getAuth`, `setAuth`, `clearAuth`)
- 헤더 자동 부착 (`Content-Type`, `Authorization`)
- JSON/텍스트 응답 파싱
- `response.ok` 또는 `is_success === false` 처리
- 예약 생성/조회/취소 경로 검증
- 상태 조회 경로 검증

**테스트 방식**
- `fetch`를 `jest.fn()`으로 모킹
- `sessionStorage`, `Headers`, `FormData`는 테스트 내부에서 shim으로 제공

---

## 5. 테스트 유틸리티 패턴

### 5.1 데이터 빌더

테스트 상단에 `slot()`, `meetingReservation()` 같은 빌더 함수를 두고 재사용합니다.

```js
const slot = (id, startHour, endHour) => ({
  id,
  startMinutes: startHour * 60,
  endMinutes: endHour * 60,
  label: `${String(startHour).padStart(2, "0")}:00 ~ ${String(endHour).padStart(2, "0")}:00`,
});
```

### 5.2 응답 더블

`api-client.test.js`에서는 응답 생성 헬퍼를 사용합니다.

- `buildJsonResponse(body, { ok, status })`
- `buildTextResponse(text, { ok, status })`

---

## 6. 테스트 추가 가이드

### 6.1 새로운 정책 추가 시

1. 실패 케이스 먼저 작성
2. 성공 케이스 최소 1개 작성
3. 메시지/코드까지 검증

### 6.2 API 호출 추가 시

1. `ApiClient` 함수 추가
2. 경로/메서드/바디 직렬화를 테스트로 고정
3. 실패 응답 케이스 포함

---

## 7. 일반 체크리스트

- [ ] 날짜/시간 경계값 테스트가 포함되어 있는가
- [ ] 실패 메시지가 실제 UI 메시지와 동일한가
- [ ] `sessionStorage` 키 변경 시 테스트를 함께 수정했는가
- [ ] 테스트가 DOM/브라우저에 의존하지 않는가

---

## 8. 상세 문서

더 자세한 케이스 목록은 아래 문서를 참고합니다.

- `docs/frontend/frontend-test.md`
