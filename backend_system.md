# Campus Seat Reservation System - Backend Implementation Report

## Table of Contents
1. [System Overview](#1-system-overview)
2. [Architecture Design](#2-architecture-design)
3. [Database Design](#3-database-design)
4. [API Endpoints](#4-api-endpoints)
5. [Business Logic](#5-business-logic)
6. [Exception Handling](#6-exception-handling)
7. [Concurrency Control](#7-concurrency-control)
8. [Scheduler System](#8-scheduler-system)
9. [Security & Authentication](#9-security--authentication)
10. [Technology Stack](#10-technology-stack)

---

## 1. System Overview

### 1.1 Project Description
RESTful API backend system for campus library seat and meeting room reservations using FastAPI framework.

### 1.2 Core Features
- **Student Login**: Authentication system based on student ID
- **Seat Reservation**: 2-hour slot seat booking (direct selection / random assignment)
- **Meeting Room Reservation**: 1-hour slot meeting room booking (with participants)
- **My Reservations**: View and cancel reservations
- **Facility Status**: Check real-time availability
- **Auto Status Update**: Scheduler-based automatic reservation status management

### 1.3 Operation Policy

| Category | Seat Reservation | Meeting Room Reservation |
|----------|------------------|--------------------------|
| **Time Unit** | 2 hours | 1 hour |
| **Operating Hours** | 09:00 - 21:00 | 09:00 - 18:00 |
| **Daily Limit** | 4 hours (240 min) | 2 hours (120 min) |
| **Weekly Limit** | - | 5 hours (300 min) |
| **Min People** | 1 person | 4 people (including owner) |

---

## 2. Architecture Design

### 2.1 Layered Architecture

```
+-------------------------------------------+
|  Endpoint Layer (Controller)              |
|  - HTTP request/response handling         |
|  - Authentication token verification      |
|  - Input data validation (Pydantic)       |
+-------------------+-----------------------+
                    |
+-------------------v-----------------------+
|  Service Layer (Business Logic)           |
|  - Business rule validation               |
|  - Reservation conflict checking          |
|  - Usage limit calculation                |
|  - Transaction management                 |
+-------------------+-----------------------+
                    |
+-------------------v-----------------------+
|  Repository/Model Layer (Data Access)     |
|  - SQLAlchemy ORM models                  |
|  - Database queries                       |
|  - Transaction commit/rollback            |
+-------------------------------------------+
```

### 2.2 Directory Structure

```
app/
├── api/                          # API router layer
│   ├── docs.py                   # Swagger documentation
│   └── v1/                       # API v1
│       ├── api.py                # Router integration
│       └── endpoints/            # Endpoints (Thin Controller)
│           ├── auth.py           # Authentication
│           ├── meeting_rooms.py  # Meeting room reservations
│           ├── reservations.py   # My reservations
│           ├── seats.py          # Seat reservations
│           └── status.py         # Facility status
│
├── auth/                         # Authentication dependencies
│   └── deps.py                   # JWT token extraction & verification
│
├── handlers/                     # Exception handling
│   └── exception_handlers.py    # Centralized exception handlers
│
├── schemas/                      # Pydantic schemas
│   ├── common.py                 # Common responses
│   ├── meeting_room.py           # Meeting room request/response
│   ├── reservation.py            # Reservation response
│   ├── seat.py                   # Seat request/response
│   ├── status.py                 # Facility status response
│   └── user.py                   # User schema
│
├── services/                     # Business logic layer
│   ├── meeting_room_service.py   # Meeting room logic
│   ├── reservation_service.py    # Reservation helpers
│   ├── seat_service.py           # Seat reservation logic
│   ├── status_service.py         # Status query logic
│   └── user_service.py           # User management
│
├── constants.py                  # Constants definition
├── database.py                   # DB connection setup
├── exceptions.py                 # Custom exception classes
├── init_db.py                    # DB initialization
├── main.py                       # FastAPI entry point
├── models.py                     # SQLAlchemy ORM models
└── scheduler.py                  # Background scheduler
```

### 2.3 Design Patterns

#### Thin Controller Pattern
```python
# Endpoint only handles HTTP processing
@router.post("/api/reservations/seats")
def create_seat_reservation(
    request: schemas.SeatReservationCreate,
    db: Session = Depends(get_db),
    student_id: int = Depends(get_current_student_id),
):
    # Delegate business logic to service
    reservation = seat_service.reserve_seat(db, student_id, request)
    return ApiResponse(is_success=True, payload=reservation)
```

#### Facade Pattern
```python
# Orchestrate complex validation logic in single function
def process_reservation(db, request, student_id):
    # 1. Room validation
    # 2. Time validation
    # 3. Conflict checking
    # 4. Limit checking
    # 5. Create reservation
    pass
```

---

## 3. Database Design

### 3.1 ERD (Entity-Relationship Diagram)

```
+-------------+         +------------------+         +--------------+
|    User     |         |   Reservation    |         | MeetingRoom  |
+-------------+         +------------------+         +--------------+
| student_id  |<--------| reservation_id   |-------->| room_id      |
|last_login_at|    1:N  | student_id (FK)  |  N:1    | min_capacity |
+-------------+         | meeting_room_id  |         | max_capacity |
                        | seat_id (FK)     |         | is_available |
                        | start_time       |         +--------------+
                        | end_time         |
                        | status           |
                        | created_at       |         +--------------+
                        +------------------+         |    Seat      |
                                |                    +--------------+
                                | 1:N                | seat_id      |
                                |                    | is_available |
                                v                    +--------------+
                    +------------------------+              ^
                    |ReservationParticipant  |              | N:1
                    +------------------------+              |
                    | id                     |--------------+
                    | reservation_id (FK)    |
                    | participant_student_id |
                    +------------------------+
```

### 3.2 Table Details

#### User
```sql
CREATE TABLE users (
    student_id INTEGER PRIMARY KEY,     -- Student ID
    last_login_at DATETIME               -- Last login time (UTC)
);
```

#### MeetingRoom
```sql
CREATE TABLE meeting_rooms (
    room_id INTEGER PRIMARY KEY,         -- Room ID (1-3)
    min_capacity INTEGER DEFAULT 3,      -- Min capacity
    max_capacity INTEGER DEFAULT 6,      -- Max capacity
    is_available BOOLEAN DEFAULT TRUE    -- Available flag
);
```

#### Seat
```sql
CREATE TABLE seats (
    seat_id INTEGER PRIMARY KEY,         -- Seat number (1-70)
    is_available BOOLEAN DEFAULT TRUE    -- Available flag
);
```

#### Reservation
```sql
CREATE TABLE reservations (
    reservation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    meeting_room_id INTEGER,
    seat_id INTEGER,
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) NOT NULL,

    FOREIGN KEY (student_id) REFERENCES users(student_id),
    FOREIGN KEY (meeting_room_id) REFERENCES meeting_rooms(room_id),
    FOREIGN KEY (seat_id) REFERENCES seats(seat_id),

    CONSTRAINT check_times CHECK (start_time < end_time),
    CONSTRAINT check_facility CHECK (
        (meeting_room_id IS NOT NULL AND seat_id IS NULL) OR
        (meeting_room_id IS NULL AND seat_id IS NOT NULL)
    )
);

-- Performance indexes
CREATE INDEX idx_student_start ON reservations(student_id, start_time);
CREATE INDEX idx_room_start ON reservations(meeting_room_id, start_time, status);
CREATE INDEX idx_seat_start ON reservations(seat_id, start_time, status);
CREATE INDEX idx_status_start ON reservations(status, start_time);
CREATE INDEX idx_status_end ON reservations(status, end_time);
```

#### ReservationParticipant
```sql
CREATE TABLE reservation_participants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reservation_id INTEGER NOT NULL,
    participant_student_id INTEGER NOT NULL,

    FOREIGN KEY (reservation_id) REFERENCES reservations(reservation_id)
        ON DELETE CASCADE,
    FOREIGN KEY (participant_student_id) REFERENCES users(student_id)
);
```

### 3.3 ReservationStatus
```python
class ReservationStatus(str, Enum):
    RESERVED = "RESERVED"    # Reserved
    IN_USE = "IN_USE"        # In use
    CANCELED = "CANCELED"    # Canceled
    COMPLETED = "COMPLETED"  # Completed
```

---

## 4. API Endpoints

### 4.1 Authentication API

#### POST /api/auth/login
**Description**: Student login (student ID based)

**Request**:
```json
{
  "student_id": 202312345
}
```

**Response**:
```json
{
  "is_success": true,
  "code": null,
  "payload": {
    "student_id": 202312345,
    "access_token": "token-202312345-abc123..."
  }
}
```

**Key Logic**:
- 9-digit student ID validation
- Ban student IDs (202099999, 202288888)
- Token generation: `token-{student_id}-{uuid}`
- Auto cookie setup (httponly, samesite=lax)
- Record login time

---

### 4.2 Seat Reservation API

#### POST /api/reservations/seats
**Description**: Seat reservation (direct selection)

**Request**:
```json
{
  "seat_id": 1,
  "date": "2025-12-20",
  "start_time": "10:00",
  "end_time": "12:00"
}
```

**Response**:
```json
{
  "is_success": true,
  "code": null,
  "payload": {
    "reservation_id": 123,
    "seat_id": 1,
    "date": "2025-12-20",
    "start_time": "10:00",
    "end_time": "12:00",
    "status": "RESERVED",
    "type": "seat"
  }
}
```

**Validation Rules**:
1. 2-hour unit (120 minutes)
2. Operating hours: 09:00-21:00
3. Seat time conflict check
4. Own seat duplication check
5. Meeting room conflict check
6. Daily 4-hour limit check

#### POST /api/reservations/seats/random
**Description**: Random seat reservation

**Random Assignment Logic**:
```sql
SELECT seat_id FROM seats
WHERE is_available = TRUE
  AND seat_id NOT IN (
    SELECT seat_id FROM reservations
    WHERE seat_id IS NOT NULL
      AND status IN ('RESERVED', 'IN_USE')
      AND start_time < :end_time
      AND end_time > :start_time
  )
ORDER BY RANDOM()
LIMIT 1;
```

---

### 4.3 Meeting Room Reservation API

#### POST /api/reservations/meeting-rooms
**Description**: Meeting room reservation

**Request**:
```json
{
  "room_id": 1,
  "date": "2025-12-20",
  "start_time": "10:00",
  "end_time": "11:00",
  "participants": [
    {"student_id": 202312346},
    {"student_id": 202312347},
    {"student_id": 202312348}
  ]
}
```

**Validation Rules**:
1. 1-hour unit (60 minutes)
2. Operating hours: 09:00-18:00
3. Min 3 participants (excluding owner)
4. Room time conflict check
5. Owner time conflict check (seat + meeting room)
6. Participant time conflict check (seat + meeting room)
7. Owner daily 2-hour limit check
8. Owner weekly 5-hour limit check
9. Participant limit check

---

### 4.4 My Reservations API

#### GET /api/reservations/me
**Description**: View my reservations

**Query Parameters**:
- `from`: Start date (optional)
- `to`: End date (optional)
- `type`: Reservation type (meeting_room | seat, optional)

#### DELETE /api/reservations/me/{reservation_id}
**Description**: Cancel reservation

**Cancellation Constraints**:
- Only RESERVED status can be canceled
- Only own reservations can be canceled

---

### 4.5 Facility Status API

#### GET /api/status/seats?date=2025-12-20
**Description**: View seat reservation status

#### GET /api/status/meeting-rooms?date=2025-12-20
**Description**: View meeting room reservation status

---

## 5. Business Logic

### 5.1 Seat Reservation Logic (seat_service.py)

#### Core Validation Flow
```python
def reserve_seat(db, student_id, request):
    """Seat reservation main logic"""

    # 1. Determine seat (direct or random)
    if request.seat_id:
        seat_id = request.seat_id
    else:
        seat_id = _find_and_lock_random_available_seat(db, start_time, end_time)

    # 2. Time conflict check
    _ensure_no_seat_conflict(db, seat_id, start_time, end_time)

    # 3. Own seat duplication check
    if check_overlap_with_other_facility(db, student_id, start_time, end_time,
                                        include_seats=True, include_meeting_rooms=False):
        raise ConflictException("Already have seat reservation at same time")

    # 4. Meeting room conflict check
    if check_overlap_with_other_facility(db, student_id, start_time, end_time,
                                        include_seats=False, include_meeting_rooms=True):
        raise ConflictException("Have meeting room reservation at same time")

    # 5. Daily limit check (4 hours)
    daily_usage = _get_daily_seat_usage_minutes(db, student_id, date)
    duration = (end_time - start_time).total_seconds() / 60
    if daily_usage + duration > SEAT_DAILY_LIMIT_MINUTES:
        raise LimitExceededException("Daily seat limit (240 min) exceeded")

    # 6. Create reservation
    reservation = create_seat_reservation(db, student_id, seat_id, start_time, end_time)
    db.commit()

    return reservation
```

---

### 5.2 Meeting Room Reservation Logic (meeting_room_service.py)

#### Core Validation Flow
```python
def process_reservation(db, request, student_id):
    """Meeting room reservation orchestration"""

    # 1. Room validation
    # 2. Participant count validation
    # 3. Time conversion (KST -> UTC)
    # 4. Room conflict check
    # 5. Owner time conflict check (seat + meeting room)
    # 6. Participant time conflict check
    # 7. Owner daily limit check
    # 8. Owner weekly limit check
    # 9. Participant limit check
    # 10. Create reservation
    pass
```

#### Weekly Usage Calculation
```python
def check_user_weekly_meeting_limit(db, student_id, date, duration):
    """Check weekly meeting room usage (Monday 00:00 ~ Sunday 23:59)"""

    # Find Monday of the week
    weekday = date.weekday()
    week_start_date = date - timedelta(days=weekday)
    week_end_date = week_start_date + timedelta(days=6)

    # Calculate total usage
    reservations = db.query(Reservation).filter(
        Reservation.student_id == student_id,
        Reservation.meeting_room_id.isnot(None),
        Reservation.status.in_([ReservationStatus.RESERVED, ReservationStatus.IN_USE]),
        Reservation.start_time < week_end_utc,
        Reservation.end_time > week_start_utc
    ).all()

    total_minutes = sum(
        (res.end_time - res.start_time).total_seconds() / 60
        for res in reservations
    )

    if total_minutes + duration > MEETING_ROOM_WEEKLY_LIMIT_MINUTES:
        raise LimitExceededException("Weekly meeting room limit (300 min) exceeded")
```

---

### 5.3 Reservation Helpers (reservation_service.py)

#### Time Conflict Check
```python
def check_overlap_with_other_facility(
    db, student_id, start_time, end_time,
    include_seats=True, include_meeting_rooms=True
):
    """
    Check if user has other facility reservations at same time

    Check scope:
    1. Reservations where user is owner (seat/meeting room)
    2. Reservations where user is participant (meeting room)
    """

    # 1. Check as owner
    query_owner = db.query(Reservation).filter(
        Reservation.student_id == student_id,
        Reservation.status.in_([ReservationStatus.RESERVED, ReservationStatus.IN_USE]),
        Reservation.start_time < end_time,
        Reservation.end_time > start_time,
    )

    if query_owner.first():
        return True

    # 2. Check as participant (meeting room only)
    if include_meeting_rooms:
        query_participant = (
            db.query(Reservation)
            .join(ReservationParticipant)
            .filter(
                ReservationParticipant.participant_student_id == student_id,
                Reservation.status.in_([ReservationStatus.RESERVED, ReservationStatus.IN_USE]),
                Reservation.start_time < end_time,
                Reservation.end_time > start_time,
            )
        )

        if query_participant.first():
            return True

    return False
```

#### Cancel Reservation
```python
def cancel_reservation(db, reservation_id, student_id):
    """Cancel reservation (with transaction lock control)"""

    try:
        # BEGIN IMMEDIATE: acquire write lock immediately
        db.execute(text("BEGIN IMMEDIATE"))

        # Query reservation
        reservation = db.query(Reservation).filter(
            Reservation.reservation_id == reservation_id
        ).first()

        # Validations
        if not reservation:
            raise BusinessException("Reservation not found")

        if reservation.student_id != student_id:
            raise ForbiddenException("Can only cancel own reservations")

        if reservation.status == ReservationStatus.CANCELED:
            raise BusinessException("Already canceled")

        if reservation.status != ReservationStatus.RESERVED:
            raise ForbiddenException("Only RESERVED status can be canceled")

        # Update status and commit
        reservation.status = ReservationStatus.CANCELED
        db.commit()  # Release lock
        db.refresh(reservation)

        return reservation

    except Exception as e:
        db.rollback()  # Rollback and release lock on error
        raise e
```

---

## 6. Exception Handling

### 6.1 Custom Exception Hierarchy

```python
BusinessException                # Base business exception
  +-- ConflictException         # 409 Conflict
  +-- ValidationException       # 400 Bad Request
  +-- LimitExceededException    # 400 Bad Request
  +-- ForbiddenException        # 403 Forbidden
```

### 6.2 Error Codes (constants.py)

```python
class ErrorCode:
    # Common validation
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    PARTICIPANT_MIN_NOT_MET = "PARTICIPANT_MIN_NOT_MET"

    # Business logic
    RESERVATION_CONFLICT = "RESERVATION_CONFLICT"
    RESERVATION_ALREADY_CANCELED = "RESERVATION_ALREADY_CANCELED"
    USAGE_LIMIT_EXCEEDED = "USAGE_LIMIT_EXCEEDED"
    DAILY_LIMIT_EXCEEDED = "DAILY_LIMIT_EXCEEDED"
    WEEKLY_LIMIT_EXCEEDED = "WEEKLY_LIMIT_EXCEEDED"
    OVERLAP_WITH_OTHER_FACILITY = "OVERLAP_WITH_OTHER_FACILITY"

    # Authentication
    AUTH_UNAUTHORIZED = "AUTH_UNAUTHORIZED"
    AUTH_FORBIDDEN = "AUTH_FORBIDDEN"
    AUTH_INVALID_STUDENT_ID = "AUTH_INVALID_STUDENT_ID"
```

### 6.3 Centralized Exception Handlers

```python
# 1. Business exception handler
async def business_exception_handler(request: Request, exc: Exception):
    http_status = {
        ConflictException: 409,
        ValidationException: 400,
        LimitExceededException: 400,
        ForbiddenException: 403,
    }.get(type(exc), 400)

    return JSONResponse(
        status_code=http_status,
        content=ApiResponse(
            is_success=False,
            code=exc.code,
            payload=ErrorPayload(message=exc.message, details=exc.details)
        ).model_dump()
    )

# 2. Pydantic validation exception handler
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Extract and clean error messages
    pass

# 3. Internal server exception handler
async def internal_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content=ApiResponse(
            is_success=False,
            code=ErrorCode.INTERNAL_SERVER_ERROR,
            payload=ErrorPayload(message="Internal server error")
        ).model_dump()
    )
```

### 6.4 Error Response Format

```json
{
  "is_success": false,
  "code": "DAILY_LIMIT_EXCEEDED",
  "payload": {
    "message": "Daily seat limit (240 min) exceeded",
    "details": {
      "current_usage": 240,
      "requested": 120,
      "limit": 240
    }
  }
}
```

---

## 7. Concurrency Control

### 7.1 SQLite WAL Mode

```python
# database.py
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# Auto-configured on connection
PRAGMA journal_mode=WAL          # Write-Ahead Logging
PRAGMA synchronous=NORMAL        # Balance performance and safety
```

**WAL Mode Benefits**:
- Concurrent reads and writes
- Multiple read transactions support
- Performance improvement (reduced disk I/O)

### 7.2 BEGIN IMMEDIATE Transaction

```python
def reserve_seat(db, student_id, request):
    """Seat reservation (with concurrency control)"""

    try:
        # Acquire write lock immediately
        db.execute(text("BEGIN IMMEDIATE"))

        # === Critical Section ===
        # 1. Determine seat
        # 2. Check conflicts
        # 3. Check limits
        # 4. Create reservation
        # =======================

        db.commit()  # Commit and release lock on success

    except Exception as e:
        db.rollback()  # Rollback and release lock on error
        raise e
```

### 7.3 Transaction Isolation Levels

| Operation | Isolation Level | Description |
|-----------|----------------|-------------|
| Create Reservation | `BEGIN IMMEDIATE` | Acquire write lock immediately |
| Cancel Reservation | `BEGIN IMMEDIATE` | Acquire write lock immediately |
| View Reservations | Default (READ) | No locking |
| View Status | Default (READ) | No locking |

### 7.4 Concurrency Scenarios

#### Scenario 1: Concurrent same seat reservation
```
User A: BEGIN IMMEDIATE -> Reserve seat 1 -> Success
User B: BEGIN IMMEDIATE -> Wait -> Try seat 1 -> Conflict detected -> Fail
```

#### Scenario 2: Concurrent random seat reservation
```
User A: BEGIN IMMEDIATE -> Random seat 5 selected -> Create reservation
User B: BEGIN IMMEDIATE -> Wait -> Random query (excluding 5) -> Seat 7 selected -> Create
```

---

## 8. Scheduler System

### 8.1 Auto Status Update Job

**Execution Frequency**: Every minute (`cron`, `minute='*'`)

```python
# scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()

def update_reservation_status():
    """Auto update reservation status"""

    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)

        # 1. Auto start: RESERVED -> IN_USE
        started = db.query(Reservation).filter(
            Reservation.status == ReservationStatus.RESERVED,
            Reservation.start_time <= now
        ).all()

        for res in started:
            res.status = ReservationStatus.IN_USE

        # 2. Auto complete: IN_USE -> COMPLETED
        completed = db.query(Reservation).filter(
            Reservation.status == ReservationStatus.IN_USE,
            Reservation.end_time <= now
        ).all()

        for res in completed:
            res.status = ReservationStatus.COMPLETED

        db.commit()

    except Exception as e:
        db.rollback()
        print(f"[Scheduler] Error: {e}")
    finally:
        db.close()
```

### 8.2 Lifecycle Management

```python
# main.py
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up application...")

    # Initialize DB
    Base.metadata.create_all(bind=engine)
    initialize_data()

    # Start scheduler
    scheduler.add_job(update_reservation_status, 'cron', minute='*')
    scheduler.start()

    yield  # Server running

    # Shutdown scheduler
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)
```

### 8.3 Status Transition Diagram

```
RESERVED -------> IN_USE -------> COMPLETED
   |                                ^
   |                                |
   +---------> CANCELED ------------+
            (User cancellation)
```

**Auto Transitions**:
- `start_time <= now` -> `RESERVED` -> `IN_USE`
- `end_time <= now` -> `IN_USE` -> `COMPLETED`

**Manual Transitions**:
- User request -> `RESERVED` -> `CANCELED`

---

## 9. Security & Authentication

### 9.1 Authentication Method

**Token Format**: `token-{student_id}-{uuid}`

```python
# Token generation
from uuid import uuid4

def create_token(student_id: int) -> str:
    return f"token-{student_id}-{uuid4().hex}"

# Example: "token-202312345-abc123def456..."
```

### 9.2 Token Verification Logic

```python
# auth/deps.py
def get_current_student_id(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
    request: Request = None,
    db: Session = Depends(get_db),
) -> int:
    """Extract and verify token from Bearer header or cookie"""

    # 1. Extract token (Authorization header > cookie)
    token = _extract_token(credentials, request)

    # 2. Format validation
    if not token.startswith("token-"):
        raise BusinessException("Invalid token format")

    # 3. Extract student ID
    parts = token.split("-", 2)
    student_id = int(parts[1])

    # 4. Verify banned student IDs and DB existence
    user_service.login_student(db, student_id)

    return student_id
```

### 9.3 Banned Student ID Policy

```python
# constants.py
BANNED_STUDENT_IDS = [202099999, 202288888]

# user_service.py
def login_student(db, student_id):
    """Login processing (block banned student IDs)"""

    if student_id in BANNED_STUDENT_IDS:
        raise BusinessException("Invalid student ID")

    user = get_or_create_user(db, student_id)
    return user
```

### 9.4 Cookie Settings

```python
# auth.py
response.set_cookie(
    key="access_token",
    value=token,
    httponly=True,       # Block JavaScript access
    samesite="lax",      # CSRF protection
    max_age=3600 * 24,   # 24 hours
    path="/"
)
```

### 9.5 CORS Configuration

```python
# main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",  # Live Server
        "http://localhost:5500",
    ],
    allow_credentials=True,  # Allow cookie transmission
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 10. Technology Stack

### 10.1 Frameworks & Libraries

| Category | Technology | Version | Purpose |
|----------|-----------|---------|---------|
| **Web Framework** | FastAPI | 0.104+ | RESTful API server |
| **ORM** | SQLAlchemy | 2.0+ | Database abstraction |
| **Database** | SQLite | 3.x | Relational database |
| **Data Validation** | Pydantic | 2.0+ | Request/response schemas |
| **Scheduler** | APScheduler | 3.10+ | Background tasks |
| **ASGI Server** | Uvicorn | 0.24+ | Async server |

### 10.2 Installation & Execution

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run production server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 10.3 API Documentation Access

- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc
- **Health Check**: http://127.0.0.1:8000/health

---

## 11. Performance Optimization

### 11.1 Database Indexes

```sql
-- Optimize student reservation queries
CREATE INDEX idx_student_start ON reservations(student_id, start_time);

-- Optimize room conflict check
CREATE INDEX idx_room_start ON reservations(meeting_room_id, start_time, status);

-- Optimize seat conflict check
CREATE INDEX idx_seat_start ON reservations(seat_id, start_time, status);

-- Optimize scheduler status updates
CREATE INDEX idx_status_start ON reservations(status, start_time);
CREATE INDEX idx_status_end ON reservations(status, end_time);
```

### 11.2 Query Optimization

#### Solve N+1 Problem
```python
# Bad: N+1 queries
reservations = db.query(Reservation).all()
for res in reservations:
    participants = res.participants  # Additional query per reservation

# Good: Eager Loading
reservations = db.query(Reservation).options(
    joinedload(Reservation.participants)
).all()
```

#### Random Seat Assignment Optimization
```python
# Bad: Python level filtering
all_seats = db.query(Seat).all()
available = [s for s in all_seats if s.is_available and not is_conflicted(s)]
random_seat = random.choice(available)

# Good: DB level filtering
random_seat = db.query(Seat).filter(
    Seat.is_available == True,
    Seat.seat_id.notin_(conflicted_seat_ids)
).order_by(func.random()).first()
```

---

## 12. Time Handling Strategy

### 12.1 Timezone Definition

```python
from datetime import timezone, timedelta

KST = timezone(timedelta(hours=9))  # UTC+9 (Korea Standard Time)
UTC = timezone.utc
```

### 12.2 Storage and Response Strategy

| Stage | Timezone | Description |
|-------|----------|-------------|
| **Client Input** | KST | "2025-12-20 10:00" |
| **DB Storage** | UTC | "2025-12-20 01:00:00 UTC" |
| **API Response** | KST | "2025-12-20 10:00:00" |

### 12.3 Conversion Logic

```python
# Input -> Storage (KST -> UTC)
def kst_to_utc(date, time_obj):
    dt_kst = datetime.combine(date, time_obj, tzinfo=KST)
    return dt_kst.astimezone(timezone.utc)

# Storage -> Response (UTC -> KST)
@field_serializer('start_time')
def serialize_dt(self, dt: datetime, _info):
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(KST).strftime("%Y-%m-%d %H:%M:%S")
```

---

## Appendix

### A. Complete API Endpoint List

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| POST | /api/auth/login | Login | No |
| GET | /seats | Get all seats | No |
| GET | /seats/{seat_id} | Get specific seat | No |
| POST | /seats | Create seat | No |
| POST | /api/reservations/seats | Reserve seat | Yes |
| POST | /api/reservations/seats/random | Random seat reservation | Yes |
| POST | /api/reservations/meeting-rooms | Reserve meeting room | Yes |
| GET | /api/reservations/me | My reservations | Yes |
| DELETE | /api/reservations/me/{id} | Cancel reservation | Yes |
| GET | /api/status/seats | Seat status | No |
| GET | /api/status/meeting-rooms | Meeting room status | No |

### B. Constants Definition

```python
# Operating hours
OperationHours.START_HOUR = 9      # 09:00
OperationHours.END_HOUR = 18       # 18:00 (meeting room)
OperationHours.SEAT_END_HOUR = 21  # 21:00 (seat)

# Reservation limits
MEETING_ROOM_SLOT_MINUTES = 60          # 1 hour
MEETING_ROOM_DAILY_LIMIT_MINUTES = 120  # 2 hours/day
MEETING_ROOM_WEEKLY_LIMIT_MINUTES = 300 # 5 hours/week
MEETING_ROOM_MIN_PARTICIPANTS = 3       # Min 3 people

SEAT_SLOT_MINUTES = 120                 # 2 hours
SEAT_DAILY_LIMIT_MINUTES = 240          # 4 hours/day

# Facility range
MEETING_ROOM_IDS = [1, 2, 3]           # 3 meeting rooms
SEAT_MIN_ID = 1
SEAT_MAX_ID = 70                        # 70 seats
```

---

**Date**: 2025-12-19
**Author**: Backend Development Team
**Version**: 1.0.0
