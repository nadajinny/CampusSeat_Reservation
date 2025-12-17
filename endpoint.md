# API 엔드포인트 코딩 가이드라인 (v2.0)

이 가이드는 **"Thin Controller & Rich Documentation"** 을 지향합니다.

컨트롤러에서 반복적인 `try-except` 구문을 제거하고, Pydantic과 FastAPI의 기능을 적극 활용하여 문서화를 자동화하는 것에 초점을 맞춥니다.

## 1. 중앙화된 예외 처리 (Centralized Exception Handling)

**핵심 변경점:** 컨트롤러(Endpoint)에서 비즈니스 예외(`BusinessException`)를 잡기 위한 `try-except` 블록을 **사용하지 않습니다.**

### 작성 규칙

1. **Service 계층**: 비즈니스 로직 위반 시 과감하게 에러를 `raise` 합니다.
2. **Controller 계층**: 에러 처리를 신경 쓰지 않고, **성공 케이스(Happy Path)** 만 작성합니다.
3. **Global Handler**: `main.py` 또는 `exception_handlers.py`에 등록된 전역 핸들러가 예외를 포착하여 표준 `ApiResponse` 실패 포맷으로 변환합니다.

### ❌ Before (기존 스타일)

Python

`# app/api/v1/endpoints/seats.py
@router.post("")
def create_seat(seat: seat_schemas.SeatCreate, db: Session = Depends(get_db)):
    try:
        # 개발자가 매번 try-except를 작성해야 함 (중복 코드)
        new_seat = seat_service.create_seat(db, seat.seat_id)
        return ApiResponse(is_success=True, payload=new_seat)
    except BusinessException as e:
        # 에러 응답 포맷팅 로직이 컨트롤러에 노출됨
        return ApiResponse(is_success=False, code=e.code, payload={"message": e.message})`

### ✅ After (개선된 스타일)

Python

`# app/api/v1/endpoints/seats.py
@router.post("", response_model=ApiResponse[seat_schemas.SeatResponse])
def create_seat(seat: seat_schemas.SeatCreate, db: Session = Depends(get_db)):
    # 성공 로직만 깔끔하게 작성
    new_seat = seat_service.create_seat(db, seat.seat_id)
    
    return ApiResponse(
        is_success=True, 
        payload=new_seat
    )
    # 예외 발생 시 전역 핸들러가 자동으로 ApiResponse(is_success=False, ...) 반환`

---

## 2. Swagger(OpenAPI) 문서화 강화

API 문서가 코드와 동기화되어 살아있는 명세서가 되도록 작성합니다.

### A. 라우터 데코레이터 활용

엔드포인트의 메타데이터를 데코레이터에 풍부하게 작성합니다.

- `summary`: API의 짧은 요약 (함수명으로 자동 생성되지만, 한글로 명시 권장)
- `description`: 상세 로직, 제약 사항, 비즈니스 규칙 설명 (Markdown 지원)
- `response_model`: 성공 시 반환될 데이터 구조 명시 (Swagger Schema 생성의 핵심)

Python

`@router.post(
    "/reservations",
    summary="회의실 예약 생성",
    description="""
    학생 계정으로 회의실을 예약합니다.
    
    - **제약 사항**:
        - 최소 3명 이상의 참여자 필요
        - 1회 최대 2시간, 주간 최대 5시간 이용 가능
        - 운영 시간(09:00~18:00) 내에서만 예약 가능
    """,
    response_model=ApiResponse[meeting_room_schemas.MeetingRoomReservationResponse],
    status_code=status.HTTP_201_CREATED
)
def create_reservation(...):
    ...`

### B. Pydantic Schema 문서화

Request/Response 모델 정의 시 `Field`를 적극 활용하여 예시 값(`example`)과 설명(`description`)을 제공합니다. 이는 프론트엔드 개발자가 API를 테스트할 때 매우 유용합니다.

Python

`# schemas/meeting_room.py
class MeetingRoomReservationCreate(BaseModel):
    room_id: int = Field(
        ..., 
        ge=1, 
        le=3, 
        description="회의실 번호 (1~3)", 
        examples=[1]  # Swagger UI에서 'Try it out' 클릭 시 기본값으로 들어감
    )
    participant_list: List[str] = Field(
        ..., 
        min_length=3,
        description="참여자 학번 목록",
        examples=[["20230001", "20230002", "20230003"]]
    )`

---

## 3. 계층별 책임 재정의 (Refined Responsibilities)

| **계층 (Layer)** | **역할 (Role)** | **스타일 가이드 (Do's & Don'ts)** |
| --- | --- | --- |
| **Endpoint**
(Controller) | - 요청 수신
- **문서화(Swagger) 정의**
- Service 호출
- **성공 응답 생성** | - **DO**: `response_model` 명시, 상세한 `description` 작성
- **DON'T**: `try-except`로 비즈니스 에러 잡기, 비즈니스 로직 구현 |
| **Service** | - 비즈니스 로직 수행
- 트랜잭션 관리
- **예외 발생(Raise)** | - **DO**: 조건 불만족 시 즉시 `raise BusinessException(...)`
- **DON'T**: HTTP 상태 코드 직접 다루기 (`HTTPException` 사용 금지) |
| **Global Handler**
(Main/Middleware) | - **예외 포착 및 응답 변환** | - `BusinessException`을 잡아 `ApiResponse(is_success=False)`로 변환
- 500 서버 에러 등 예상치 못한 에러 로깅 |

---

## 4. 예시 코드 (Full Example)

**app/api/v1/endpoints/meeting_rooms.py**

Python

`from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from ....schemas import meeting_room as schemas
from ....schemas.common import ApiResponse
from ....services import meeting_room_service
from ....database import get_db

router = APIRouter(prefix="/meeting-rooms", tags=["Meeting Rooms"])

@router.post(
    "/reservations",
    summary="회의실 예약 요청",
    description="주어진 날짜와 시간에 회의실을 예약합니다. 참여자는 최소 3명이어야 합니다.",
    response_model=ApiResponse[schemas.ReservationResponse], # [중요] Generic 타입 명시
    status_code=status.HTTP_201_CREATED
)
def create_meeting_room_reservation(
    request: schemas.MeetingRoomReservationCreate,
    db: Session = Depends(get_db)
):
    # [스타일] try-except 없이 바로 서비스 호출
    # 예외 발생 시 Global Exception Handler가 처리함
    reservation = meeting_room_service.process_reservation(
        db=db,
        request=request,
        student_id=202312345 # TODO: Auth 미들웨어 연동 시 교체
    )

    # [스타일] 성공 응답만 반환
    return ApiResponse(
        is_success=True,
        payload=reservation
    )`

### 참고: 전역 핸들러 구현 예시 (main.py 등에 추가)

가이드라인 적용을 위해 아래와 같은 핸들러가 `main.py`에 설정되어 있어야 합니다.

Python

`# app/exception_handlers.py (예시)
from fastapi import Request, status
from fastapi.responses import JSONResponse
from .exceptions import BusinessException
from .schemas.common import ApiResponse

async def business_exception_handler(request: Request, exc: BusinessException):
    return JSONResponse(
        status_code=status.HTTP_200_OK, # 또는 에러 종류에 따라 400 등 분기 가능
        content=ApiResponse(
            is_success=False,
            code=exc.code,
            payload={"message": exc.message}
        ).model_dump()
    )

# main.py에서 등록
# app.add_exception_handler(BusinessException, business_exception_handler)`

이 가이드라인을 따름으로써 코드는 훨씬 "선언적"으로 변하며, API 문서는 코드를 수정함과 동시에 자동으로 최신화되는 효과를 얻을 수 있습니다.