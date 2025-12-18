# 🧭 주요 화면 흐름

FastAPI 백엔드와 상호작용하는 프런트 화면을 **6단계 플로우**로 나누어 설명합니다.  
각 화면은 `js/app.js`의 초기화 함수와 `ApiClient` 래퍼를 통해 데이터를 주고받으며, 로그인 세션이나 `pendingReservation`이 없다면 즉시 로그인/검색 화면으로 이동합니다.

---

## 1. `login.html` – 세션 발급

| 단계 | 설명 |
| --- | --- |
| 입력 | 학번, 비밀번호(폼 검증용). 학번은 9자리 숫자만 허용하며, 잘못된 학번(`202099999`, `202288888`)은 클라이언트 단계에서 차단합니다. |
| API 호출 | `POST /api/auth/login` – 성공 시 `payload.student_id`, `payload.access_token` 수신. |
| 상태 저장 | 응답을 `sessionStorage.studentId / accessToken`에 저장 후 `dashboard.html`로 이동. |
| 오류 처리 | FastAPI가 반환하는 `payload.message`를 그대로 화면에 보여주며, 폼 입력 강조와 포커스 이동을 수행합니다. |

비밀번호는 실제 서버 검증에는 사용하지 않지만, 폼 UX를 위해 필수 입력으로 유지합니다.

---

## 2. `dashboard.html` – 허브

- DOMContentLoaded 시 `sessionStorage.studentId`가 없으면 즉시 `login.html`로 리다이렉트합니다.
- `renderUserSummary`가 헤더에 학번을 표시하고, `bindLogout`이 세션 스토리지를 모두 지운 뒤 로그인 페이지로 돌려보냅니다.
- 예약 가능 조회, 내 예약 관리 페이지 링크만 제공하며 별도 API 호출은 하지 않습니다.

---

## 3. `search-availability.html` – 조건 선택 & 현황 조회

1. **필터 선택**  
   - 시설 유형 라디오 버튼과 날짜 입력을 감시합니다. 두 값이 모두 존재해야 다음 단계가 노출됩니다.

2. **현황 조회 API**  
   - 회의실: `GET /api/status/meeting-rooms?date=YYYY-MM-DD`  
   - 열람실: `GET /api/status/seats?date=YYYY-MM-DD`
   - 로딩 중에는 섹션별 안내 문구를 보여주고, 실패 시 오류 메시지를 해당 영역에 렌더링합니다.

3. **시간대 선택 UI**  
   - 회의실: 현황 데이터를 기반으로 가능한 슬롯을 버튼 목록으로 출력합니다. 사용자가 클릭하면 즉시 회의실 예약 페이지로 이동합니다.
   - 열람실: 슬롯을 격자 형태로 표시하고 최대 2개까지 선택할 수 있도록 제약합니다. `ReservationEngine.slotsListOverlap`을 활용하여 겹치는 슬롯은 즉시 비활성화합니다.

4. **상태 저장 & 이동**  
   - 선택된 정보(`type`, `date`, `slot`, `slots`)를 `pendingReservation` key에 JSON 문자열로 저장 후 `meeting-room-reservation.html` 또는 `seat-reservation.html`로 이동합니다.

---

## 4. `meeting-room-reservation.html` – 회의실 확정

| 단계 | 세부 내용 |
| --- | --- |
| 컨텍스트 복원 | `pendingReservation`에서 날짜/슬롯을 읽어 카드에 표시. 데이터가 없으면 경고와 함께 검색 페이지 링크 제공. |
| 회의실 목록 | `MEETING_ROOMS` 상수(회의실 1~3, 정원 정보 포함)를 카드로 렌더링. 향후 백엔드 연동 시 API 대체 예정. |
| 참여자 입력 | 최소 3명의 학번을 텍스트 필드로 입력. 공란/포맷 오류는 ReservationEngine 결과를 통해 안내합니다. |
| 검증 | `validateMeeting`이 운영시간/중복/일·주 한도, 참여자 수, 학번 형식을 검사. 실패 시 메시지를 alert 및 페이지 내 오류영역에 표시합니다. |
| API 호출 | `POST /api/reservations/meeting-rooms`. 성공 시 `pendingReservation`을 삭제하고 완료 메시지를 띄운 뒤 대시보드로 이동합니다. |

---

## 5. `seat-reservation.html` – 좌석 확정

- `pendingReservation.slots`를 목록으로 표시하고, 없으면 검색 화면으로 안내합니다.
- 좌석 맵은 서버 데이터가 준비되기 전까지는 더미 데이터를 사용하지만, 설계상 `ApiClient.fetchSeatStatus` 응답을 그대로 활용하도록 되어 있습니다.
- 선택한 좌석 ID와 시간대 리스트를 `validateSeat`에 전달하여 중복/시간 제한을 검증합니다.
- 예약 버튼은 `POST /api/reservations/seats` 호출, 랜덤 배정 버튼은 `/api/reservations/seats/random`을 호출합니다.
- 성공/실패 여부에 따라 `pendingReservation`을 정리하고 사용자에게 토스트/알림을 제공합니다.

---

## 6. `my-reservations.html` – 조회 및 취소

| 기능 | 구현 포인트 |
| --- | --- |
| 목록 조회 | `GET /api/reservations/me` (필터가 있을 경우 querystring 포함). 반환된 `payload.items`를 테이블로 렌더링하며, 상태에 따라 Pill 스타일 클래스를 적용합니다. |
| 필터 | 기간(from/to)와 유형(type)을 submit 시 URLSearchParams로 변환하여 API에 전달합니다. 초기화 버튼은 필드 값을 비우고 즉시 재조회합니다. |
| 취소 | 각 행의 “취소” 버튼은 `/api/reservations/me/{id}` DELETE 호출. 성공 시 목록을 다시 로드하고, 실패 시 오류 메시지를 상태 영역에 표시합니다. |
| 세션 검사 | 다른 화면과 동일하게 학번/토큰이 없으면 로그인 페이지로 이동합니다. |

---

### 공통 규칙

- 모든 화면은 진입 시점에 `sessionStorage.studentId` 존재 여부를 먼저 확인합니다.
- API 호출은 반드시 `ApiClient`를 통해 이루어지며, Access Token 자동 첨부와 표준 오류 메시지를 재사용합니다.
- 백엔드 정책(운영시간, 좌석 규칙 등)이 변경되면 검색/예약 단계뿐 아니라 ReservationEngine과 테스트도 함께 수정해야 일관성이 보장됩니다.
