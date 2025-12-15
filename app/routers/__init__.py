"""
routers package
===============
This package contains all API route modules.

Each file in this folder defines a set of related API endpoints.
For example:
- seats.py: Endpoints for seat operations
- meeting_rooms.py: Endpoints for meeting room reservations
- auth.py: Authentication endpoints
"""

from . import auth, seats, meeting_rooms

__all__ = ["auth", "seats", "meeting_rooms"]
