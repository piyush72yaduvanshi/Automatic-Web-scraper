"""Health check endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
import redis

from app.core.database import get_db
from app.core.config import settings
from app.schemas.common import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint.
    
    Returns the health status of the service and its dependencies.
    """
    # Check database
    try:
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    # Check Redis (optional)
    redis_status = None
    try:
        redis_client = redis.from_url(str(settings.REDIS_URL))
        redis_client.ping()
        redis_status = "healthy"
    except Exception:
        redis_status = "unavailable"
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "database": db_status,
        "redis": redis_status,
        "version": "1.0.0",
    }
