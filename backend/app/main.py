"""
main.py - Application Entry Point
"""
import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.scheduler import scheduler, update_reservation_status
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
    
    scheduler.add_job(update_reservation_status, 'cron', minute='*')
    scheduler.start()
    
    print("🕒 Scheduler started.")
    
    yield
    
    scheduler.shutdown()
    print("🕒 Shutting down scheduler...")
    print("👋 Shutting down application...")

# 2. FastAPI 앱 생성 (중복 제거됨)
app = FastAPI(
    title="Library Seat Reservation System",
    description="API for reserving seats and meeting rooms",
    version="1.0.0",
    lifespan=lifespan
)

# 3. CORS 설정 - 정적 HTML 페이지(예: http://127.0.0.1:5500)와 연동
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1",
        "http://localhost",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4. 예외 핸들러 등록 (순서 중요)
app.add_exception_handler(BusinessException, business_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, internal_exception_handler)

# 5. 라우터 등록
app.include_router(api_router)

# 6. 정적 파일 서빙 설정
# frontend 디렉터리 경로 (backend/app/main.py 기준으로 상위 두 단계 -> 프로젝트 루트 -> frontend)
FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"

# 정적 파일(css, js) 서빙 - API 라우터보다 후순위로 등록
if FRONTEND_DIR.exists():
    app.mount("/css", StaticFiles(directory=FRONTEND_DIR / "css"), name="css")
    app.mount("/js", StaticFiles(directory=FRONTEND_DIR / "js"), name="js")

# 7. 기본 엔드포인트
@app.get("/health")
def health_check():
    return {"status": "healthy"}

# 8. HTML 페이지 라우팅 (SPA 스타일이 아닌 개별 페이지 서빙)
@app.get("/")
def serve_index():
    """루트 경로 - index.html 서빙"""
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "Welcome to the Library Seat Reservation System!", "docs": "/docs"}

@app.get("/login")
@app.get("/login.html")
def serve_login():
    """로그인 페이지"""
    return FileResponse(FRONTEND_DIR / "login.html")

@app.get("/dashboard")
@app.get("/dashboard.html")
def serve_dashboard():
    """대시보드 페이지"""
    return FileResponse(FRONTEND_DIR / "dashboard.html")

@app.get("/seat-reservation")
@app.get("/seat-reservation.html")
def serve_seat_reservation():
    """좌석 예약 페이지"""
    return FileResponse(FRONTEND_DIR / "seat-reservation.html")

@app.get("/meeting-room-reservation")
@app.get("/meeting-room-reservation.html")
def serve_meeting_room_reservation():
    """회의실 예약 페이지"""
    return FileResponse(FRONTEND_DIR / "meeting-room-reservation.html")

@app.get("/my-reservations")
@app.get("/my-reservations.html")
def serve_my_reservations():
    """내 예약 페이지"""
    return FileResponse(FRONTEND_DIR / "my-reservations.html")

@app.get("/search-availability")
@app.get("/search-availability.html")
def serve_search_availability():
    """좌석 검색 페이지"""
    return FileResponse(FRONTEND_DIR / "search-availability.html")
