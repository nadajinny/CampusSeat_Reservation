# 🎨 프런트엔드 개요

정적 HTML과 순수 JavaScript만으로 구성된 UI 계층을 빠르게 파악하기 위한 개요 문서입니다.  
세부 실행 방법, 화면 흐름, 스토리지 정책 등은 `frontend-*.md` 개별 문서로 분리되어 있으니 상황에 따라 참고하세요.

---

## 📂 폴더 구조 (`frontend/`)

```
frontend/
├── css/style.css                 # 공통 스타일
├── js/
│   ├── api-client.js             # 백엔드 API 통신 래퍼
│   ├── app.js                    # 화면별 초기화 & 상태 관리
│   └── reservation-engine.js     # 좌석/회의실 제약 검증 로직
├── __tests__/reservation-engine.test.js
├── login.html
├── dashboard.html
├── search-availability.html
├── meeting-room-reservation.html
├── seat-reservation.html
└── my-reservations.html
```

`index.html`은 초기 와이어프레임 역할이며 실제 플로우는 `login → dashboard → (search/seat/meeting/my-reservations)` 순서를 따릅니다.
