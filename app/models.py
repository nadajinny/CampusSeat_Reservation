"""
models.py - SQLAlchemy Database Models
======================================
This module defines the database tables using SQLAlchemy ORM.

Key Concepts for Students:
- Each class represents a table in the database
- Each attribute represents a column in the table
- SQLAlchemy automatically handles the mapping between Python objects and SQL
"""

from sqlalchemy import Column, Integer, Boolean

from .database import Base


# ---------------------------------------------------------------------------
# Seat Model
# ---------------------------------------------------------------------------
class Seat(Base):
    """
    Represents a seat in the library that can be reserved.

    Table name: 'seats'

    Columns:
        seat_id: Unique identifier for the seat (1, 2, 3, ... 70)
        is_active: Whether the seat is available for reservation

    Example:
        seat = Seat(seat_id=1, is_active=True)
    """

    # The name of the table in the database
    __tablename__ = "seats"

    # ---------------------------------------------------------------------------
    # Column Definitions
    # ---------------------------------------------------------------------------

    # Primary key - unique identifier for each seat
    # autoincrement=False: We manually set seat IDs (1-70), not auto-generated
    seat_id = Column(Integer, primary_key=True, autoincrement=False)

    # Whether the seat is active/available
    # default=True: New seats are active by default
    is_active = Column(Boolean, default=True)

    def __repr__(self):
        """String representation for debugging"""
        return f"<Seat(seat_id={self.seat_id}, is_active={self.is_active})>"
