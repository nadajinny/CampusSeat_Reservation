"""
database.py - Database Connection Setup
========================================
This module handles the SQLite database connection using SQLAlchemy.

Key Concepts for Students:
- Engine: The starting point for SQLAlchemy, manages the connection pool
- SessionLocal: A factory that creates new database sessions
- get_db: A dependency that provides a session and ensures cleanup
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# ---------------------------------------------------------------------------
# Database URL Configuration
# ---------------------------------------------------------------------------
# SQLite database file will be created in the project root directory
# The three slashes (///) indicate a relative path
SQLALCHEMY_DATABASE_URL = "sqlite:///./library_reservation.db"

# ---------------------------------------------------------------------------
# Create the SQLAlchemy Engine
# ---------------------------------------------------------------------------
# The engine is the core interface to the database
#
# connect_args={"check_same_thread": False}:
#   - SQLite by default only allows one thread to communicate with it
#   - FastAPI uses multiple threads, so we need to disable this check
#   - This is safe because SQLAlchemy manages connections properly
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# ---------------------------------------------------------------------------
# Create a Session Factory
# ---------------------------------------------------------------------------
# SessionLocal is a class that will create new Session objects when called
# - autocommit=False: We control when to commit transactions
# - autoflush=False: We control when to flush changes to the database
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ---------------------------------------------------------------------------
# Create a Base Class for Models
# ---------------------------------------------------------------------------
# All our SQLAlchemy models will inherit from this Base class
# It provides the mapping between Python classes and database tables
Base = declarative_base()


# ---------------------------------------------------------------------------
# Database Dependency
# ---------------------------------------------------------------------------
def get_db():
    """
    Dependency function that provides a database session.

    How it works:
    1. Creates a new database session
    2. Yields it to the endpoint (the endpoint uses it)
    3. After the endpoint finishes, closes the session (cleanup)

    Usage in endpoints:
        @router.get("/items/")
        def read_items(db: Session = Depends(get_db)):
            # use db here
            pass

    The 'yield' keyword makes this a generator, which FastAPI uses
    to ensure the session is properly closed after each request.
    """
    db = SessionLocal()
    try:
        yield db  # Provide the session to the endpoint
    finally:
        db.close()  # Always close the session, even if an error occurred
