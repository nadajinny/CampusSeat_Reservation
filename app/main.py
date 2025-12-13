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

from contextlib import asynccontextmanager

from fastapi import FastAPI

from .database import engine, SessionLocal, Base
from .routers import seats
from . import crud, schemas


# ---------------------------------------------------------------------------
# Lifespan Context Manager
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages application startup and shutdown events.

    Startup (before yield):
        - Create database tables
        - Initialize default data (seats 1-70)

    Shutdown (after yield):
        - Cleanup resources if needed

    Why use lifespan instead of @app.on_event?
        - @app.on_event is deprecated in newer FastAPI versions
        - lifespan provides cleaner resource management
        - It's the recommended modern approach
    """
    # =========================================================================
    # STARTUP: Code here runs when the application starts
    # =========================================================================

    print("🚀 Starting up the application...")

    # Create all database tables
    # This reads all models that inherit from Base and creates their tables
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")

    # Initialize seats if the database is empty
    initialize_seats()

    # Yield control to the application (app runs while yielded)
    yield

    # =========================================================================
    # SHUTDOWN: Code here runs when the application stops
    # =========================================================================
    print("👋 Shutting down the application...")


def initialize_seats():
    """
    Initialize seats 1-70 if they don't exist.

    This function runs on every startup but only creates seats
    if the database is empty. This ensures we always have seats
    available for reservation.
    """
    # Create a new database session
    db = SessionLocal()

    try:
        # Check if any seats exist
        seats_count = crud.get_seats_count(db)

        if seats_count == 0:
            print("📝 No seats found. Creating seats 1-70...")

            # Create seats with IDs from 1 to 70
            for seat_id in range(1, 71):
                seat_data = schemas.SeatCreate(seat_id=seat_id, is_active=True)
                crud.create_seat(db, seat_data)

            print("✅ Successfully created 70 seats!")
        else:
            print(f"ℹ️  Found {seats_count} existing seats. Skipping initialization.")

    finally:
        # Always close the session
        db.close()


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
    This project uses a simplified layered architecture:
    - **Router** → API endpoints
    - **CRUD** → Database operations (pure functions)
    - **Models** → SQLAlchemy database tables
    - **Schemas** → Pydantic validation models
    """,
    version="1.0.0",
    lifespan=lifespan  # Register the lifespan manager
)



# ---------------------------------------------------------------------------
# Include Routers
# ---------------------------------------------------------------------------
# This adds all the endpoints from the seats router to our app
app.include_router(seats.router)


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
