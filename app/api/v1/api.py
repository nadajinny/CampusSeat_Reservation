"""
api/v1/api.py - API v1 Router Aggregator
========================================
모든 v1 API 라우터를 하나로 통합합니다.
"""

from fastapi import APIRouter

from .endpoints import auth, seats, meeting_rooms

api_router = APIRouter()

# Auth 라우터 (prefix: /api/auth)
api_router.include_router(auth.router, prefix="/api")

# Seats 라우터 (prefix: /seats)
api_router.include_router(seats.router)

# Meeting Rooms 라우터 (prefix: /api/reservations/meeting-rooms)
api_router.include_router(meeting_rooms.router, prefix="/api")
