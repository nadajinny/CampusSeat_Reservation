# 🗄️ Database Schema & ERD

이 문서는 시설 예약 시스템의 데이터베이스 스키마를 정의합니다.

ORM Framework: SQLAlchemy

Database: SQLite (Production: PostgreSQL Recommended)

> ⚠️ 중요: 시간 데이터 처리 정책
> 
> - **DB 저장 (Storage):** 모든 `DateTime` 필드는 **UTC (Coordinated Universal Time)** 기준으로 저장합니다. (`timezone=True`)
> - **사용자 표시 (Display):** 클라이언트에게 응답할 때(Pydantic) **KST (UTC+9)**로 변환하여 전달합니다.

---

## 📌 1. Enums (열거형 타입)

DB에 저장되는 상태값들의 정의입니다.

| Enum Name | Key | Value | 설명 |
| --- | --- | --- | --- |
| **ReservationStatus** | `RESERVED` | `"RESERVED"` | 예약 완료 (기본값) |
|  | `IN_USE` | `"IN_USE"` | 사용 중 (입실) |
|  | `CANCELED` | `"CANCELED"` | 예약 취소 |
|  | `COMPLETED` | `"COMPLETED"` | 이용 완료 (퇴실) |

---

## 👤 2. Users (사용자)

학생 및 관리자 계정 정보를 관리합니다.

- **Table Name**: `users`
- **PK**: `student_id`

| **컬럼명 (Column)** | **타입 (Type)** | **Nullable** | **설명 (Description)** |
| --- | --- | --- | --- |
| **student_id** | `Integer` | ❌ No | **PK**. 학번 (자동증가 아님, 수동 입력) |
| **last_login_at** | `DateTime(TZ)` | ✅ Yes | 마지막 로그인 시각 (UTC). 
 *가입 직후에는 `NULL` 상태임.* |

---

## 🏢 3. MeetingRooms (회의실)

예약 가능한 회의실 정보입니다. (총 3개 운영 예정)

- **Table Name**: `meeting_rooms`
- **PK**: `room_id`

| **컬럼명 (Column)** | **타입 (Type)** | **Nullable** | **기본값** | **설명** |
| --- | --- | --- | --- | --- |
| **room_id** | `Integer` | ❌ No | - | **PK**. 회의실 번호 (1~3) |
| **min_capacity** | `Integer` | ❌ No | `3` | 최소 이용 인원 |
| **max_capacity** | `Integer` | ❌ No | `6` | 최대 이용 인원 |
| **is_available** | `Boolean` | ❌ No | `True` | 이용 가능 여부 (점검 중일 때 False) |

---

## 🪑 4. Seats (좌석)

개인 학습용 좌석 정보입니다. (총 70개 운영 예정)

- **Table Name**: `seats`
- **PK**: `seat_id`

| **컬럼명 (Column)** | **타입 (Type)** | **Nullable** | **기본값** | **설명** |
| --- | --- | --- | --- | --- |
| **seat_id** | `Integer` | ❌ No | - | **PK**. 좌석 번호 (1~70) |
| **is_available** | `Boolean` | ❌ No | `True` | 이용 가능 여부 |

---

## 📅 5. Reservations (예약 통합)

회의실과 좌석 예약을 통합 관리하는 테이블입니다.

- **Table Name**: `reservations`
- **PK**: `reservation_id`

> 💡 핵심 제약 조건 (Business Logic in DB)
> 
> 1. **시간 검증 (`check_time_order`)**: `start_time`은 무조건 `end_time`보다 과거여야 합니다.
> 2. **배타적 예약 (`check_exclusive_facility`)**: 예약은 **회의실** 또는 **좌석** 둘 중 하나만 가능합니다. (둘 다 NULL이거나 둘 다 값이 있으면 에러 발생)

| **컬럼명 (Column)** | **타입 (Type)** | **Nullable** | **FK** | **설명** |
| --- | --- | --- | --- | --- |
| **reservation_id** | `Integer` | ❌ No | - | **PK**. 예약 고유 번호 (Auto Increment) |
| **student_id** | `Integer` | ❌ No | `users.student_id` | 예약자 학번 |
| **meeting_room_id** | `Integer` | ✅ Yes | `meeting_rooms.room_id` | 회의실 예약 시 값 존재 |
| **seat_id** | `Integer` | ✅ Yes | `seats.seat_id` | 좌석 예약 시 값 존재 |
| **start_time** | `DateTime(TZ)` | ❌ No | - | 시작 시간 (**UTC**) |
| **end_time** | `DateTime(TZ)` | ❌ No | - | 종료 시간 (**UTC**) |
| **created_at** | `DateTime(TZ)` | ❌ No | - | 생성 일시 (**UTC**) |
| **status** | `Enum` | ❌ No | - | 예약 상태 (`RESERVED` 등) |

**인덱스 (Indexes)**

- `idx_student_start`: (`student_id`, `start_time`) - 내 예약 조회용
- `idx_room_start`: (`meeting_room_id`, `start_time`, `status`) - 회의실 현황 조회용
- `idx_seat_start`: (`seat_id`, `start_time`, `status`) - 좌석 현황 조회용

---

## 👥 6. ReservationParticipants (회의실 참여자)

회의실 예약 시 동반 참여자를 저장하는 테이블입니다. (N:M 해소)

- **Table Name**: `reservation_participants`
- **PK**: `id`

| **컬럼명 (Column)** | **타입 (Type)** | **Nullable** | **FK** | **설명** |
| --- | --- | --- | --- | --- |
| **id** | `Integer` | ❌ No | - | **PK**. 고유 ID |
| **reservation_id** | `Integer` | ❌ No | `reservations.id` | 예약 정보 (**CASCADE**: 예약 삭제 시 같이 삭제됨) |
| **participant_student_id** | `Integer` | ❌ No | `users.student_id` | 참여자 학번 |

---

## 🔗 Relationships (객체 관계)

SQLAlchemy ORM에서 사용하는 관계 매핑입니다.

- **Users** ↔ **Reservations**: `1:N` (한 학생이 여러 예약을 가짐)
- **Reservations** ↔ **Participants**: `1:N` (한 예약에 여러 참여자가 있음)
    - *Note: `back_populates`가 설정되어 있어, 예약 객체에 참여자를 `append`하면 자동으로 `reservation_id`가 매핑됩니다.*