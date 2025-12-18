"""
api/v1/api.py - API v1 Router Aggregator
========================================
Registers all version 1 routers in the FastAPI application.
"""

from fastapi import APIRouter

from .endpoints import auth, seats, meeting_rooms, status, reservations

api_router = APIRouter()

# Auth routes (/api/auth)
api_router.include_router(auth.router, prefix="/api")

# Seat routes (/seats)
api_router.include_router(seats.router)

# Seat reservation routes (/api/reservations/seats)
api_router.include_router(seats.reservation_router, prefix="/api")

# Meeting-room routes (/api/reservations/meeting-rooms)
api_router.include_router(meeting_rooms.router, prefix="/api")

# My reservations routes (/api/reservations/me)
api_router.include_router(reservations.router, prefix="/api")

# Status routes (/api/status)
api_router.include_router(status.router, prefix="/api")
