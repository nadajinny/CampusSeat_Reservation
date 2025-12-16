"""
main.py - Application Entry Point
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from app.database import engine, Base
from app.init_db import initialize_data
from app.api.v1 import api_router
from app.exceptions import BusinessException
from app.handlers.exception_handlers import (
    business_exception_handler,
    validation_exception_handler,
    internal_exception_handler
)

# 1. Lifespan: 서버 시작/종료 로직
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting up application...")
    Base.metadata.create_all(bind=engine)
    initialize_data()
    yield
    print("👋 Shutting down application...")

# 2. FastAPI 앱 생성 (중복 제거됨)
app = FastAPI(
    title="Library Seat Reservation System",
    description="API for reserving seats and meeting rooms",
    version="1.0.0",
    lifespan=lifespan
)

# 3. 예외 핸들러 등록 (순서 중요)
app.add_exception_handler(BusinessException, business_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, internal_exception_handler)

# 4. 라우터 등록
app.include_router(api_router)

# 5. 기본 엔드포인트
@app.get("/")
def read_root():
    return {
        "message": "Welcome to the Library Seat Reservation System!",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}