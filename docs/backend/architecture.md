# 🏗️ 백엔드 아키텍처 및 폴더 구조 (FastAPI)

우리 프로젝트는 초보자도 이해하기 쉽고 개발 속도를 높이기 위해 **"Service 계층을 생략한 실용적인 3단 구조"**를 사용합니다.

### 📂 프로젝트 폴더 구조

아래 구조를 그대로 따라가세요. 파일 위치가 헷갈릴 때 참고하세요.

Plaintext

`📂 backend/app
 ├── 📜 main.py          # 1. 앱 실행 & 설정 (가장 바깥, 진입점)
 ├── 📜 database.py      # 2. DB 연결 설정 (Session 관리)
 ├── 📜 models.py        # 3. DB 테이블 정의 (SQLAlchemy - 창고지기)
 ├── 📜 schemas.py       # 4. 데이터 검증/전송 객체 (Pydantic - 포장지)
 ├── 📜 crud.py          # 5. 실제 DB 작업 함수들 (DB 조회/저장 - 실무자)
 └── 📂 routers          # 6. API 엔드포인트 (URL 정의 - 접수원)
      ├── 📜 seats.py
      ├── 📜 users.py
      └── 📜 reservations.py`

---

### 🔄 아키텍처 흐름 (3단계)

사용자 요청이 들어오면 딱 **3단계**만 거칩니다.

> 1. Router (routers/*.py) : "손님 맞이 (접수원)"
> 
> - URL 주소(`/seats`)와 데이터(`schemas`)를 받습니다.
> - 복잡한 생각 안 합니다. 데이터만 확인하고 바로 **CRUD 함수**를 부릅니다.
> 
> **2. CRUD (`crud.py`) : "실무 처리 (작업자)"**
> 
> - Router가 시킨 실제 일(DB 저장, 조회, 수정)을 수행합니다.
> - 어려운 클래스(`Class`) 안 씁니다. 그냥 **함수(`def`)**로 만듭니다.
> 
> **3. Model (`models.py`) : "데이터 정의 (창고지기)"**
> 
> - DB 테이블이 어떻게 생겼는지 정의만 합니다.

---

### 💻 코드 구현 가이드 (Copy & Paste)

가장 중요한 파일 3개의 작성 예시입니다. 이 패턴을 모든 기능(유저, 예약 등)에 똑같이 적용하면 됩니다.

### 1. Schemas (`backend/app/schemas.py`)

데이터가 들어오고 나갈 때의 **포장지(모양)**를 정의합니다.

Python

`from pydantic import BaseModel

# 1. 사용자에게서 받을 데이터 모양 (Request)
class SeatCreate(BaseModel):
    seat_id: int

# 2. 사용자에게 보여줄 데이터 모양 (Response)
class SeatResponse(BaseModel):
    seat_id: int
    is_active: bool`

### 2. CRUD (`backend/app/crud.py`)

복잡한 클래스 없이 **함수**로 DB 로직을 짭니다. (Service + Repository 역할 통합)

Python

`from sqlalchemy.orm import Session
from . import models, schemas

# 좌석 조회 함수 (Read)
def get_seat(db: Session, seat_id: int):
    return db.query(models.Seat).filter(models.Seat.seat_id == seat_id).first()

# 좌석 생성 함수 (Create)
def create_seat(db: Session, seat: schemas.SeatCreate):
    # 모델(창고지기)을 불러와서 데이터를 채움
    db_seat = models.Seat(seat_id=seat.seat_id)
    
    db.add(db_seat)      # DB에 추가
    db.commit()          # 저장 확정
    db.refresh(db_seat)  # 새로고침 (ID 등 자동생성 값 받기)
    
    return db_seat`

### 3. Router (`backend/app/routers/seats.py`)

URL을 만들고 CRUD 함수를 연결합니다.

Python

`from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app import crud, schemas, database

# 라우터 생성
router = APIRouter()

# URL: POST /seats/
@router.post("/seats/", response_model=schemas.SeatResponse)
def create_seat(seat: schemas.SeatCreate, db: Session = Depends(database.get_db)):
    # 복잡한 로직 없이 바로 CRUD 함수 호출!
    return crud.create_seat(db=db, seat=seat)`

---

### 🌟 이 구조를 사용하는 이유 (Team Benefits)

- **🧠 생각의 흐름과 일치:** `"URL 들어옴(Router) -> DB 작업함(CRUD) -> 결과 줌"`으로 직관적이라 이해하기 쉽습니다.
- **⚡️ 복붙(Copy-Paste) 개발:** `seats.py` 하나만 잘 짜면, `users.py`, `reservations.py`는 변수명만 바꿔서 금방 만들 수 있습니다.
- **🛡️ 충돌 방지:** `main.py`에 코드를 다 때려 넣지 않고 `routers/` 폴더로 나눴기 때문에, 팀원끼리 파일이 겹쳐서 에러 날 일이 적습니다.

---

### 🚀 To-Do: 팀원들이 해야 할 일

1. `backend/app/crud.py` 파일 생성하기
2. `backend/app/routers/` 폴더 만들고 안에 `seats.py` 만들기
3. 위 코드 복사해서 붙여넣고 서버 실행(`run.bat`) 해보기!
