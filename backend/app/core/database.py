"""Database configuration and session management."""

import logging
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from app.core.config import settings

logger = logging.getLogger(__name__)

db_url = str(settings.DATABASE_URL)

# Configure engine arguments safely based on dialect
engine_kwargs = {
    "echo": settings.DEBUG,
}

if db_url.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    engine_kwargs.update({
        "pool_pre_ping": True,
        "pool_size": settings.DATABASE_POOL_SIZE,
        "max_overflow": settings.DATABASE_MAX_OVERFLOW,
    })

# Create database engine with fallback handling
try:
    engine = create_engine(db_url, **engine_kwargs)
except Exception as e:
    logger.warning(f"Failed to create database engine with configured DATABASE_URL: {e}. Falling back to SQLite.")
    fallback_url = "sqlite:///./crm_leads.db"
    engine = create_engine(fallback_url, connect_args={"check_same_thread": False}, echo=settings.DEBUG)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for declarative models using modern SQLAlchemy 2.0 API
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get database session.
    
    Yields:
        Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)

