"""
crud.py - Database Operations (CRUD Functions)
===============================================
This module contains pure functions for database operations.

CRUD stands for:
- Create: Add new records to the database
- Read: Retrieve records from the database
- Update: Modify existing records
- Delete: Remove records from the database

Key Concepts for Students:
- These are pure functions, NOT classes
- Each function takes a database session as the first argument
- Functions are simple and do one thing well
- This keeps the code easy to understand and test

Why pure functions instead of classes?
- Simpler to understand for beginners
- No need to manage object state
- Easier to test in isolation
- Clear input -> output relationship
"""

from sqlalchemy.orm import Session

from . import models, schemas


# ---------------------------------------------------------------------------
# READ Operations
# ---------------------------------------------------------------------------

def get_seat(db: Session, seat_id: int) -> models.Seat | None:
    """
    Get a single seat by its ID.

    Args:
        db: Database session
        seat_id: The ID of the seat to find

    Returns:
        Seat object if found, None if not found

    Example:
        seat = get_seat(db, seat_id=1)
        if seat:
            print(f"Found seat {seat.seat_id}")
        else:
            print("Seat not found")
    """
    return db.query(models.Seat).filter(models.Seat.seat_id == seat_id).first()


def get_all_seats(db: Session) -> list[models.Seat]:
    """
    Get all seats from the database.

    Args:
        db: Database session

    Returns:
        List of all Seat objects, ordered by seat_id

    Example:
        seats = get_all_seats(db)
        for seat in seats:
            print(f"Seat {seat.seat_id}: active={seat.is_active}")
    """
    return db.query(models.Seat).order_by(models.Seat.seat_id).all()


def get_seats_count(db: Session) -> int:
    """
    Count the total number of seats in the database.

    Args:
        db: Database session

    Returns:
        Total count of seats

    Example:
        count = get_seats_count(db)
        print(f"Total seats: {count}")
    """
    return db.query(models.Seat).count()


# ---------------------------------------------------------------------------
# CREATE Operations
# ---------------------------------------------------------------------------

def create_seat(db: Session, seat: schemas.SeatCreate) -> models.Seat:
    """
    Create a new seat in the database.

    Args:
        db: Database session
        seat: SeatCreate schema with seat data

    Returns:
        The newly created Seat object

    Example:
        new_seat = SeatCreate(seat_id=1, is_active=True)
        created = create_seat(db, new_seat)
        print(f"Created seat with ID: {created.seat_id}")

    Process:
        1. Create a SQLAlchemy model instance from Pydantic data
        2. Add it to the session (staged for insert)
        3. Commit the transaction (actually write to DB)
        4. Refresh to get any DB-generated values
        5. Return the created object
    """
    # Create SQLAlchemy model instance
    # model_dump() converts Pydantic model to dictionary
    db_seat = models.Seat(**seat.model_dump())

    # Add to session (staged, not yet in DB)
    db.add(db_seat)

    # Commit transaction (write to DB)
    db.commit()

    # Refresh to get the latest data from DB
    db.refresh(db_seat)

    return db_seat
