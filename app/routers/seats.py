"""
routers/seats.py - API Endpoints for Seats
==========================================
This module defines the REST API endpoints for seat operations.

Key Concepts for Students:
- Router: Groups related endpoints together
- Endpoints: Functions that handle HTTP requests
- Depends: FastAPI's dependency injection system
- Response models: Define what the API returns

Endpoint Summary:
- POST /seats/  : Create a new seat
- GET  /seats/  : List all seats
- GET  /seats/{seat_id} : Get a specific seat
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db


# ---------------------------------------------------------------------------
# Create the Router
# ---------------------------------------------------------------------------
# prefix: All endpoints in this router will start with /seats
# tags: Groups endpoints in the Swagger UI documentation
router = APIRouter(
    prefix="/seats",
    tags=["Seats"]
)


# ---------------------------------------------------------------------------
# POST /seats/ - Create a new seat
# ---------------------------------------------------------------------------
@router.post("/", response_model=schemas.SeatResponse, status_code=status.HTTP_201_CREATED)
def create_seat(
    seat: schemas.SeatCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new seat.

    - **seat_id**: Unique identifier for the seat (required, >= 1)
    - **is_active**: Whether the seat is active (optional, default: true)

    Returns the created seat data.
    Raises 400 error if seat_id already exists.
    """
    # Check if seat already exists
    existing_seat = crud.get_seat(db, seat_id=seat.seat_id)
    if existing_seat:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Seat with id {seat.seat_id} already exists"
        )

    # Create and return the new seat
    return crud.create_seat(db=db, seat=seat)


# ---------------------------------------------------------------------------
# GET /seats/ - List all seats
# ---------------------------------------------------------------------------
@router.get("/", response_model=list[schemas.SeatResponse])
def read_seats(db: Session = Depends(get_db)):
    """
    Get all seats.

    Returns a list of all seats ordered by seat_id.
    """
    seats = crud.get_all_seats(db)
    return seats


# ---------------------------------------------------------------------------
# GET /seats/{seat_id} - Get a specific seat
# ---------------------------------------------------------------------------
@router.get("/{seat_id}", response_model=schemas.SeatResponse)
def read_seat(
    seat_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific seat by ID.

    - **seat_id**: The ID of the seat to retrieve

    Returns the seat data.
    Raises 404 error if seat not found.
    """
    seat = crud.get_seat(db, seat_id=seat_id)
    if seat is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Seat with id {seat_id} not found"
        )
    return seat
