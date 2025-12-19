# ✅ 프런트엔드 테스트 문서

프런트엔드는 **DOM 의존성이 없는 순수 로직**을 `frontend/js/`에 두고 Jest로 단위 테스트합니다.  
이 문서는 **어디를 어떻게 테스트하고 있는지**, **테스트를 확장하는 방법**을 정리합니다.

---

## 1. 테스트 환경

| 항목 | 설명 |
| --- | --- |
| 러너 | Jest (CommonJS) |
| 위치 | `frontend/__tests__/*.test.js` |
| 엔트리 | `npm test` (`jest --runInBand`) |
| Node 버전 | 18+ 권장 |

---

## 2. 테스트 목적

- 예약 정책/시간 계산 로직의 회귀 방지
- API 호출 규칙(헤더/경로/에러 처리) 검증
- UI 로직을 순수 함수로 분리하기 위한 기준 제공

---

## 3. 테스트 위치

```
frontend/__tests__/
├── reservation-engine.test.js
└── api-client.test.js
```

---

## 4. 실행 방법

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

## 5. ReservationEngine 테스트 커버리지

**대상 파일**
- `frontend/js/reservation-engine.js`

### 5.1 회의실(`validateMeeting`)

| 케이스 | 목적 |
| --- | --- |
| 인증되지 않은 요청 거부 | `userId` 없이 호출 시 실패하는지 확인 |
| 과거 날짜 거부 | 과거 날짜 예약 차단 |
| 참여자 최소 인원 | 참여자 3명 미만 실패 |
| 참여자 학번 형식 | 9자리 숫자 검증 |
| 동일 사용자 중복 예약 | 같은 사용자·시간 중복 차단 |
| 다른 시설 시간 겹침 | 좌석 예약과 겹치는지 검사 |
| 회의실 선점 여부 | 동일 회의실 중복 차단 |
| 일일 이용 한도 | 1일 2시간 초과 차단 |
| 주간 이용 한도 | 주간 5시간 초과 차단 |
| 참여자 정규화 | 공백 제거 및 정규화 확인 |

### 5.2 열람실 좌석(`validateSeat`)

| 케이스 | 목적 |
| --- | --- |
| 인증 필요 | 로그인 없으면 실패 |
| 시간대 선택 필수 | 슬롯 미선택 실패 |
| 시간대 개수 제한 | 2개 슬롯 초과 실패 |
| 겹치는 슬롯 금지 | 중복 슬롯 차단 |
| 과거 날짜 거부 | 과거 예약 차단 |
| 운영 시간 검증 | 운영 시간 외 차단 |
| 좌석 ID 필수 | 좌석 선택 누락 차단 |
| 좌석 선점 여부 | 동일 좌석 중복 차단 |
| 회의실과 중복 시간 | 타 시설 예약과 겹침 차단 |
| 일일 이용 한도 | 1일 4시간 초과 차단 |
| 유효한 예약 허용 | 정상 입력 성공 확인 |

### 5.3 공통 유틸리티

| 케이스 | 목적 |
| --- | --- |
| 슬롯 겹침 경계 | 끝-시작이 맞닿으면 비겹침 |
| 슬롯 겹침 감지 | 부분 겹침 판정 |
| 리스트 겹침 감지 | 슬롯 리스트 중복 감지 |
| 날짜 파싱 | 잘못된 문자열 null 처리 |
| 과거 날짜 판정 | 잘못된 날짜는 false |
| 주간 범위 | 월요일~일요일 범위 계산 |
| 주간 합산 | 같은 주 예약만 합산 |
| 좌석 가용성 | 좌석/슬롯 누락 시 false |
| 사용자 충돌 | 사용자 겹침 예약 감지 |
| 회의실 선점 | 동일 회의실/슬롯 확인 |

---

## 6. ApiClient 테스트 커버리지

**대상 파일**
- `frontend/js/api-client.js`

| 케이스 | 목적 |
| --- | --- |
| 인증 상태 관리 | `getAuth`, `setAuth`, `clearAuth` 검증 |
| 헤더 자동 부착 | `Content-Type`, `Authorization` 확인 |
| 응답 파싱 | JSON/텍스트 파싱 확인 |
| 오류 처리 | `response.ok` 및 `is_success` 처리 |
| 로그인 플로우 | 학번 정규화/토큰 저장 |
| 예약 생성 | 회의실/좌석 예약 경로 검증 |
| 예약 조회 | 쿼리 직렬화 규칙 확인 |
| 예약 취소 | DELETE 경로 검증 |
| 상태 조회 | 회의실/좌석 상태 경로 확인 |

**테스트 방식**
- `fetch`를 `jest.fn()`으로 모킹
- `sessionStorage`, `Headers`, `FormData`는 테스트 내부에서 shim 제공

---

## 7. 테스트 유틸리티 패턴

### 7.1 데이터 빌더

테스트 상단에 `slot()`, `meetingReservation()` 같은 빌더 함수를 두고 재사용합니다.

```js
const slot = (id, startHour, endHour) => ({
  id,
  startMinutes: startHour * 60,
  endMinutes: endHour * 60,
  label: `${String(startHour).padStart(2, "0")}:00 ~ ${String(endHour).padStart(2, "0")}:00`,
});
```

### 7.2 응답 더블

`api-client.test.js`에서는 응답 생성 헬퍼를 사용합니다.

- `buildJsonResponse(body, { ok, status })`
- `buildTextResponse(text, { ok, status })`

---

## 8. 테스트 추가 가이드

### 8.1 새로운 정책 추가 시

1. 실패 케이스 먼저 작성
2. 성공 케이스 최소 1개 작성
3. 메시지/코드까지 검증

### 8.2 API 호출 추가 시

1. `ApiClient` 함수 추가
2. 경로/메서드/바디 직렬화를 테스트로 고정
3. 실패 응답 케이스 포함

---

## 9. 일반 체크리스트

- [ ] 날짜/시간 경계값 테스트가 포함되어 있는가
- [ ] 실패 메시지가 실제 UI 메시지와 동일한가
- [ ] `sessionStorage` 키 변경 시 테스트를 함께 수정했는가
- [ ] 테스트가 DOM/브라우저에 의존하지 않는가

---

## 10. 문제 해결 체크리스트

- `Cannot find module` 오류 → `module.exports`/경로 확인
- 타임존 문제 → `setHours(0,0,0,0)` 기준 맞추기
- 테스트 속도 저하 → 픽스처 크기 축소 또는 `--watch` 활용
