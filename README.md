# Seat & Meeting Room Reservation System

대학교 캠퍼스 내 **회의실 및 열람실 좌석**을 효율적으로 예약·관리하기 위한 웹 기반 예약 시스템입니다.  
학생과 관리자를 구분한 역할 기반 기능을 제공하며, 예약 충돌 방지와 이용 시간 제한 정책을 통해 공정한 시설 이용을 지원합니다.

---

## 📌 Project Overview

- **Project Type**: Software Engineering Course Project
- **Purpose**: 캠퍼스 시설(회의실, 열람실 좌석)의 체계적인 예약 및 관리
- **Target Users**: 학생, 관리자
- **Reservation Units**
  - 회의실: 1시간 단위
  - 열람실 좌석: 2시간 단위

---

## ✨ Key Features

### 👤 Student Features
- 날짜별 **예약 가능 시간 조회**
- **회의실 예약**
  - 최소 3명 이상 참여
  - 일일 최대 2시간 / 주간 최대 5시간
- **열람실 좌석 예약**
  - 하루 최대 4시간
  - 좌석 직접 선택 또는 랜덤 배정
- **내 예약 관리**
  - 예약 목록 조회
  - 시작 전 예약 취소 가능

### 🛠 Administrator Features
- 기간별 **전체 예약 조회**
- 시설 유형(회의실/좌석) 기준 필터링 및 정렬
- 기존 예약 **수정**
  - 시간, 날짜, 시설, 참여자 명단 변경
  - 운영시간 및 중복 예약 검증

---

## 🧭 Use Case Structure

| Use Case | Description |
|----------|-------------|
| Search Availability | 날짜별 예약 가능 시간 조회 |
| Meeting Room Reservation | 회의실 예약 |
| Seat Reservation | 열람실 좌석 예약 |
| Manage Own Reservations | 내 예약 조회 및 취소 |
| View All Reservations | 관리자 전체 예약 조회 |
| Modify Reservation | 관리자 예약 수정 |

---

## 🗂 Data Model (Overview)

### Main Entities
- **Student**
- **MeetingRoom**
- **Seat**
- **Reservation**

예약 엔티티는 다음 정보를 포함합니다:
- 예약자 학번
- 시설 유형 및 번호
- 시작/종료 시간
- 참여자 명단(회의실)
- 생성 시각

---

## 🔐 Security & Constraints

- 학번 기반 사용자 인증
- 세션 기반 접근 제어
- 관리자/학생 권한 분리
- HTTPS 기반 데이터 전송
- 운영시간: **09:00 ~ 18:00**
- 예약 중복 및 시간 초과 자동 검증

---

## 🖥 UI Structure

본 레포지토리는 **HTML 기반 화면 구조**를 중심으로 구성되어 있습니다.

- 예약 가능 시간 조회 화면
- 회의실 예약 화면
- 좌석 예약 화면
- 내 예약 관리 화면
- 관리자 예약 조회 / 수정 화면

※ 현재는 UI 구조 중심이며, CSS 및 JavaScript는 단계적으로 확장 예정입니다.

---

## 🚀 How to Run

1. **Install & bootstrap backend**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate        # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Run FastAPI (port 8000)**

   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

   → API docs: http://127.0.0.1:8000/docs  
   → 로그인·예약 API를 제공하는 백엔드. 항상 8000 포트에서 실행되어야 합니다.

3. **Serve the frontend on port 5500 (same origin for every page)**

   ```bash
   # project root에서 실행해야 /js, /css, *.html 전체가 노출됩니다.
   python3 -m http.server 5500
   ```

   → 브라우저 주소: http://127.0.0.1:5500/login.html  
   → 로그인/예약/조회 페이지들은 모두 이 주소(127.0.0.1:5500)에서 열어야 세션 스토리지를 공유하여 `accessToken`이 유지됩니다. (localhost나 file:// 로 열면 토큰이 공유되지 않습니다.)

4. **Usage flow**

   1. 브라우저에서 http://127.0.0.1:5500/login.html 접속 → 학번 로그인 (FastAPI에서 토큰 발급).  
   2. 로그인 후 같은 탭에서 dashboard → search-availability / my-reservations 등으로 이동.  
   3. 모든 API 요청은 http://127.0.0.1:8000 로 향하므로 백엔드 서버가 종료되지 않았는지 확인합니다.

> Tip: 백엔드와 프런트 서버는 서로 다른 포트를 사용해도 되지만, **정적 페이지는 항상 동일한 host:port(127.0.0.1:5500)** 에서 열어야 로그인 토큰이 유지됩니다.

---

## 📁 Project Structure

```
.
├── index.html        # 전체 화면 구조 (학생/관리자)
├── README.md
└── docs/
    └── SRS.pdf       # Software Requirements Specification (optional)
```

---

## 📌 Future Improvements

- JavaScript 기반 입력 검증 및 상태 관리
- 백엔드 연동 (DB / API)
- 역할 기반 페이지 분리
- UI/UX 개선 및 반응형 디자인
- 예약 통계 및 로그 관리 기능

---

## 🧑‍💻 Team

소프트웨어공학 프로젝트 5조  
Computer & Artificial Intelligence  
Jeonbuk National University


---

## 📄 License

This project is for educational purposes as part of a Software Engineering course.
# Seat & Meeting Room Reservation System

대학교 캠퍼스 내 **회의실 및 열람실 좌석**을 효율적으로 예약·관리하기 위한 웹 기반 예약 시스템입니다.  
학생과 관리자를 구분한 역할 기반 기능을 제공하며, 예약 충돌 방지와 이용 시간 제한 정책을 통해 공정한 시설 이용을 지원합니다.

---

## 📌 Project Overview

- **Project Type**: Software Engineering Course Project
- **Purpose**: 캠퍼스 시설(회의실, 열람실 좌석)의 체계적인 예약 및 관리
- **Target Users**: 학생, 관리자
- **Reservation Units**
  - 회의실: 1시간 단위
  - 열람실 좌석: 2시간 단위

---

## ✨ Key Features

### 👤 Student Features
- 날짜별 **예약 가능 시간 조회**
- **회의실 예약**
  - 최소 3명 이상 참여
  - 일일 최대 2시간 / 주간 최대 5시간
- **열람실 좌석 예약**
  - 하루 최대 4시간
  - 좌석 직접 선택 또는 랜덤 배정
- **내 예약 관리**
  - 예약 목록 조회
  - 시작 전 예약 취소 가능

### 🛠 Administrator Features
- 기간별 **전체 예약 조회**
- 시설 유형(회의실/좌석) 기준 필터링 및 정렬
- 기존 예약 **수정**
  - 시간, 날짜, 시설, 참여자 명단 변경
  - 운영시간 및 중복 예약 검증

---

## 🧭 Use Case Structure

| Use Case | Description |
|----------|-------------|
| Search Availability | 날짜별 예약 가능 시간 조회 |
| Meeting Room Reservation | 회의실 예약 |
| Seat Reservation | 열람실 좌석 예약 |
| Manage Own Reservations | 내 예약 조회 및 취소 |
| View All Reservations | 관리자 전체 예약 조회 |
| Modify Reservation | 관리자 예약 수정 |

---

## 🗂 Data Model (Overview)

### Main Entities
- **Student**
- **MeetingRoom**
- **Seat**
- **Reservation**

예약 엔티티는 다음 정보를 포함합니다:
- 예약자 학번
- 시설 유형 및 번호
- 시작/종료 시간
- 참여자 명단(회의실)
- 생성 시각

---

## 🔐 Security & Constraints

- 학번 기반 사용자 인증
- 세션 기반 접근 제어
- 관리자/학생 권한 분리
- HTTPS 기반 데이터 전송
- 운영시간: **09:00 ~ 18:00**
- 예약 중복 및 시간 초과 자동 검증

---

## 🧠 Reservation Engine & Validation (NEW)

프런트엔드의 모든 예약 흐름은 `js/reservation-engine.js`에 정의된 **ReservationEngine** 클래스를 통해 검증됩니다.  
객체지향 기반 설계로, 공통 규칙과 시설별 제약을 정확한 순서로 평가합니다.

### 공통 거부 규칙
- 인증되지 않은 요청
- 운영 시간(09:00~18:00) 위반
- 과거 날짜 예약
- 동일 사용자 중복 시간 예약(회의실/열람실 구분 없이)

### 회의실 전용
- 참여자 3명 미만
- 회의실 중복 예약
- 일일 2시간 초과 / 주간 5시간 초과

### 열람실 좌석 전용
- 2시간 슬롯 최대 2개 초과
- 슬롯 미선택 or 겹치는 슬롯
- 좌석 중복 예약
- 일일 총 4시간 초과
- 랜덤 배정 시 좌석 없음

모든 검증 실패는 코드/메시지 형태로 반환되어 UI에서 즉시 피드백합니다.

---

## 🧪 Automated Tests (TDD)

- `__tests__/reservation-engine.test.js`에 Jest 기반 단위 테스트 21개가 포함되어 있으며,
  모든 예약 거부 시나리오와 정상 플로우를 검증합니다.
- `npm test` 명령으로 실행되며, CI/TDD 사이클을 유지하는 데 필수입니다.
- 테스트 추가 시 ReservationEngine을 중심으로 새로운 케이스를 손쉽게 확장할 수 있습니다.

---

## 🖥 UI Structure

본 레포지토리는 **HTML 기반 화면 구조**를 중심으로 구성되어 있습니다.

- 예약 가능 시간 조회 화면
- 회의실 예약 화면
- 좌석 예약 화면
- 내 예약 관리 화면
- 관리자 예약 조회 / 수정 화면

※ 현재는 UI 구조 중심이며, CSS 및 JavaScript는 단계적으로 확장 예정입니다.

---

## 🚀 How to Run

1. **Backend API (FastAPI) 실행**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate        # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   uvicorn app.main:app --reload --port 8000
   ```

   FastAPI 서버가 http://127.0.0.1:8000 에서 실행 중이어야 로그인/예약 관리 화면이 정상 동작합니다.

2. **정적 프런트엔드 실행**

   ```bash
   python3 -m http.server 5500
   # http://127.0.0.1:5500/login.html (또는 dashboard.html)
   ```

   원하는 HTML(`dashboard.html`, `seat-reservation.html` 등)을 여는 것은 동일하며,
   백엔드 연동이 필요한 페이지(login, my-reservations)는 자동으로 FastAPI API를 호출합니다.

---

## 📁 Project Structure

```
.
├── dashboard.html                # 학생/관리자 공용 대시보드
├── login.html                    # 로그인 화면
├── search-availability.html      # 예약 가능 시간 조회
├── meeting-room-reservation.html # 회의실 예약
├── seat-reservation.html         # 열람실 좌석 예약
├── my-reservations.html          # 내 예약 관리
├── css/
│   └── style.css
├── js/
│   ├── app.js                 # UI 상태 & 이벤트
│   └── reservation-engine.js  # 예약 검증 로직 (OOP/TDD)
├── __tests__/                 # Jest 단위 테스트
│   └── reservation-engine.test.js
├── package.json               # npm scripts (npm install / npm test)
├── .gitignore                 # node_modules 등 민감/빌드 산출물 제외
└── README.md
```

---

## 📌 Future Improvements

- JavaScript 기반 입력 검증 및 상태 관리
- 백엔드 연동 (DB / API)
- 역할 기반 페이지 분리
- UI/UX 개선 및 반응형 디자인
- 예약 통계 및 로그 관리 기능

---

## 🧑‍💻 Team

소프트웨어공학 프로젝트 5조  
Computer & Artificial Intelligence  
Jeonbuk National University


---

## 📄 License

This project is for educational purposes as part of a Software Engineering course.

---

## 🧰 Development Setup

1. **Install dependencies** (once per machine)

   ```bash
   npm install
   ```

2. **Run unit tests (ReservationEngine TDD suite)**

   ```bash
   npm test
   ```

3. **Static assets / local preview**

   ```bash
   python3 -m http.server 5500
   # open http://localhost:5500/
   ```

> `node_modules/`와 빌드 산출물은 `.gitignore`에 포함되어 있으므로, 저장소를 새로 클론한 뒤 반드시 `npm install`을 실행해 개발 의존성을 설치하세요.

---
