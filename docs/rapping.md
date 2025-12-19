# 공통 응답 래핑 활용법

### 1단계: `schemas.py`에 공통 껍데기(Wrapper) 만들기

`typing.Generic`을 사용하여 **"내용물(`T`)만 갈아 끼울 수 있는 만능 상자"**를 만듭니다.

Python

`# schemas.py

from typing import Generic, TypeVar, Optional, List
from pydantic import BaseModel, Field

# 1. 제네릭 타입 변수 선언 ('T'라는 이름의 빈칸)
T = TypeVar('T')

# 2. 공통 응답 스키마 정의
class ApiResponse(BaseModel, Generic[T]):
    """
    모든 API 응답을 감싸는 공통 래퍼(Wrapper)
    - is_success: 성공 여부
    - message: 결과 메시지
    - payload: 실제 데이터 (Generic T)
    """
    is_success: bool = Field(True, description="요청 성공 여부")
    message: str = Field("요청이 성공적으로 처리되었습니다.", description="결과 메시지")
    
    # 여기가 핵심! T 타입의 데이터가 들어감 (없을 수도 있음 -> Optional)
    payload: Optional[T] = Field(None, description="실제 응답 데이터")`

---

### 2단계: 라우터(`meeting_rooms.py`)에 적용하기

이제 라우터에서 `response_model`을 정의할 때 **`ApiResponse[실제스키마]`** 형태로 감싸주기만 하면 됩니다.

### 수정 전 (AS-IS)

Python

`@router.post("", response_model=schemas.MeetingRoomReservationResponse)
def create_reservation(...):
    # ...
    return reservation # DB 객체 리턴`

### 수정 후 (TO-BE)

Python

`# meeting_rooms.py

# 1. response_model에 제네릭 적용 (대괄호 사용)
@router.post("", response_model=schemas.ApiResponse[schemas.MeetingRoomReservationResponse])
def create_meeting_room_reservation(
    request: schemas.MeetingRoomReservationCreate,
    db: Session = Depends(get_db)
):
    # ... (검증 및 DB 생성 로직: 이전과 동일) ...
    
    # crud 함수는 DB 객체(Reservation 모델)를 반환함
    new_reservation = crud.create_meeting_room_reservation(db, ...)

    # 2. 공통 응답 객체로 감싸서 리턴
    return schemas.ApiResponse(
        is_success=True,
        message="회의실 예약이 완료되었습니다.",
        payload=new_reservation  # DB 객체를 넣으면 Pydantic이 알아서 변환!
    )`

---

### 3단계: 리스트(List) 반환할 때 적용법

목록 조회 API의 경우 `List`와 함께 사용하면 됩니다.

Python

`from typing import List

# ApiResponse[ List[실제스키마] ] 형태
@router.get("", response_model=schemas.ApiResponse[List[schemas.MeetingRoomReservationResponse]])
def get_reservations(db: Session = Depends(get_db)):
    reservations = crud.get_all_reservations(db)
    
    return schemas.ApiResponse(
        message="예약 목록 조회 성공",
        payload=reservations
    )`

---

### 4단계: Swagger UI 확인

이렇게 적용하고 Swagger UI (`/docs`)를 확인해 보면, 응답 예시(Example Value)가 아래와 같이 **자동으로 구조화**되어 나타납니다.

JSON

`{
  "is_success": true,
  "message": "회의실 예약이 완료되었습니다.",
  "payload": {
    "reservation_id": 1,
    "room_id": 3,
    "start_time": "2023-12-25T14:00:00",
    "end_time": "2023-12-25T15:00:00",
    "status": "RESERVED",
    "participant_count": 5
  }
}`

### ✅ 요약: 핵심 포인트

1. **`schemas.py`**: `Generic[T]`를 상속받은 `ApiResponse` 클래스를 딱 한 번만 정의합니다.
2. **`router` 데코레이터**: `response_model=schemas.ApiResponse[내스키마]` 처럼 대괄호로 감쌉니다.
3. **`return`**: `return schemas.ApiResponse(payload=데이터)` 형태로 반환합니다.

이 패턴을 사용하면 프론트엔드 개발자가 **"항상 `payload` 안만 확인하면 데이터가 있다"**는 규칙을 갖게 되어 협업 효율이 매우 높아집니다.