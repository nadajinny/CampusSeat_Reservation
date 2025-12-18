# 📝 FastAPI 백엔드 개발 가이드라인 (Convention)

## 1. 아키텍처 및 역할 분리 (Separation of Concerns)

**"라우터는 길 찾기만, 로직은 서비스가, 검증은 문지기가 한다."**

- **Router (`api/endpoints`):** 요청을 받고 응답을 내보내는 역할만 합니다. 비즈니스 로직(검증, 계산, DB 조작)을 절대 포함하지 않습니다.
- **Schema (`schemas.py`):** 데이터의 형태와 유효성(Validation)을 책임집니다.
- **CRUD/Service (`crud.py`):** 실제 DB 작업과 핵심 비즈니스 로직을 수행합니다.

**❌ [Bad] 라우터가 너무 뚱뚱함**

Python

`@router.post("/reservations")
def create_reservation(req: Request):
    if req.time < 9: return "Error"  # 라우터가 검증함 (Bad)
    db.add(...)                      # 라우터가 DB 조작함 (Bad)`

**✅ [Good] 역할 분리**

Python

`@router.post("/reservations")
def create_reservation(req: Schema, db: Session):
    # 검증은 Schema에서 이미 끝남
    return crud.create_reservation(db, req) # 로직은 CRUD에게 위임`

---

## 2. 데이터 검증 (Pydantic 100% 활용)

**"데이터 검증은 함수 내부가 아니라, 함수 진입 전(Schema)에 끝낸다."**

- 단순 타입 체크 외에 **길이, 범위, 정규식, 복합 조건** 등은 모두 Pydantic Validator로 처리합니다.
- 라우터 내부의 `if`문으로 유효성 검사를 하지 마세요.

**❌ [Bad] 함수 내 수동 검증**

Python

`# 라우터 내부
if len(participants) < 3:
    raise HTTPException(...)`

**✅ [Good] 스키마 Validator 사용**

Python

`# schemas.py
@field_validator('participants')
def check_min_participants(cls, v):
    if len(v) < 3: raise ValueError("최소 3명 필요")
    return v`

---

## 3. 응답 처리 (Response Handling)

**"일일이 매핑하지 말고, 객체 통째로 던져라."**

- `response_model`을 반드시 명시합니다.
- DB 객체(ORM)를 JSON으로 변환하는 작업은 수동으로 하지 않고, Pydantic의 `from_attributes=True` (구 `orm_mode`)를 이용합니다.

**❌ [Bad] 수동 매핑 (노가다)**

Python

`return {
    "id": user.id,
    "name": user.name,
    # 필드 추가될 때마다 여기도 고쳐야 함
}`

**✅ [Good] 자동 변환**

Python

`# Decorator에 모델 지정
@router.get("/user", response_model=UserResponse)
def get_user():
    user = crud.get_user(db)
    return user  # DB 객체 그대로 리턴하면 끝`

---

## 4. 예외 처리 (Error Handling)

**"리턴으로 에러를 퉁치지 말고, 정확한 예외를 던져라."**

- 함수에서 `return {"success": False}`를 반환하지 않습니다.
- 문제가 생기면 즉시 `raise HTTPException` (또는 커스텀 예외)을 발생시킵니다.
- 최종적인 에러 응답 포맷(JSON)은 `main.py`의 **전역 예외 핸들러(Global Exception Handler)**가 담당합니다.

**❌ [Bad] 200 OK인 척하는 에러**

Python

`if conflict:
    return {"code": 409, "msg": "Error"} # HTTP Status는 200이라 프론트가 헷갈림`

**✅ [Good] 명확한 예외 발생**

Python

`if conflict:
    raise HTTPException(status_code=409, detail="중복된 예약")`