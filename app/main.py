"""
main.py - Application Entry Point
=================================
This is the main entry point for the FastAPI application.

Key Concepts for Students:
- FastAPI(): Creates the application instance
- lifespan: Manages startup and shutdown events
- include_router: Adds route modules to the app

How to run:
    uvicorn app.main:app --reload

Then visit:
    http://127.0.0.1:8000/docs  (Swagger UI)
    http://127.0.0.1:8000/redoc (ReDoc)
"""

# app/main.py
from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.database import SessionLocal, engine, Base
from app import models
from app.init_db import initialize_data
from app.api.v1 import api_router  # (예시) 라우터들이 모여있는 곳

# 1. Lifespan: 서버 시작/종료 시 실행될 로직 정의
@asynccontextmanager
async def lifespan(app: FastAPI):
    # [Startup] 서버 시작 시 실행
    print("🚀 Starting up application...")
    
    Base.metadata.create_all(bind=engine)
    
    # DB 세션을 열고 초기화 로직 실행 후 즉시 닫음
    initialize_data()
    
    yield  # 애플리케이션 가동 중...
    
    # [Shutdown] 서버 종료 시 실행 (필요 시 작성)
    print("👋 Shutting down application...")

# 2. FastAPI 앱 생성
app = FastAPI(
    title="Seat Reservation System",
    description="API for reserving seats and meeting rooms",
    version="1.0.0",
    lifespan=lifespan  # 정의한 lifespan 주입
)


# ---------------------------------------------------------------------------
# Create FastAPI Application
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Library Seat Reservation System",
    description="""
    A simple API for managing library seat reservations.

    ## Features
    - View all available seats
    - Create new seats
    - Check specific seat status

    ## Architecture
    This project uses a domain-driven layered architecture:
    - **api/v1/endpoints** → API endpoints by domain
    - **services** → Business logic by domain
    - **schemas** → Pydantic validation models by domain
    - **models** → SQLAlchemy database tables
    """,
    version="1.0.0",
    lifespan=lifespan  # Register the lifespan manager
)



# ---------------------------------------------------------------------------
# Include Routers
# ---------------------------------------------------------------------------
# This adds all the endpoints from the aggregated API router
app.include_router(api_router)


# ---------------------------------------------------------------------------
# Root Endpoint
# ---------------------------------------------------------------------------
@app.get("/")
def read_root():
    """
    Root endpoint - Welcome message.

    Returns a simple welcome message to confirm the API is running.
    """
    return {
        "message": "Welcome to the Library Seat Reservation System!",
        "docs": "/docs",
        "redoc": "/redoc"
    }


# ---------------------------------------------------------------------------
# Health Check Endpoint
# ---------------------------------------------------------------------------
@app.get("/health")
def health_check():
    """
    Health check endpoint.

    Useful for monitoring and load balancers to verify the app is running.
    """
    return {"status": "healthy"}
