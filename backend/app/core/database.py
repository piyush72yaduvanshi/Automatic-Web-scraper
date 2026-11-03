"""Database configuration and session management."""

import logging
from typing import Generator
from sqlalchemy import create_engine, text
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
        "pool_recycle": getattr(settings, "DATABASE_POOL_RECYCLE", 3600),
    })

# Create database engine with fallback handling
try:
    engine = create_engine(db_url, **engine_kwargs)
    # Test connection eagerly if non-sqlite to detect credentials or offline service
    if not db_url.startswith("sqlite"):
        with engine.connect() as test_conn:
            pass
except Exception as e:
    logger.warning(f"Configured database engine ({db_url}) unavailable ({e}). Falling back to SQLite.")
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
    """Initialize database tables and pgvector extension."""
    import app.models  # Ensure all model tables are registered in Base.metadata
    if not db_url.startswith("sqlite"):
        try:
            with engine.connect() as conn:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                conn.commit()
                logger.info("pgvector extension initialized successfully in PostgreSQL.")
        except Exception as e:
            logger.warning(f"Could not enable pgvector extension on database engine: {e}")

    Base.metadata.create_all(bind=engine)
