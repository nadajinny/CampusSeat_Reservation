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

1. **Clone Repository**

   ```bash
   git clone https://github.com/your-username/seat-room-reservation-system.git
   ```

2. **Open Dashboard (or Any Screen)**

   ```bash
   open dashboard.html
   ```

   또는 `seat-reservation.html`, `meeting-room-reservation.html` 등 원하는 화면을 더블 클릭하여 브라우저에서 바로 실행

3. **(Optional) Local Server**

   ```bash
   python3 -m http.server 5500
   # http://localhost:5500/dashboard.html
   ```

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
│   └── app.js
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
