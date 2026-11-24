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
    
    # Check MinIO (optional)
    minio_status = None
    try:
        from minio import Minio
        minio_endpoint = getattr(settings, 'MINIO_ENDPOINT', None)
        if minio_endpoint:
            minio_client = Minio(
                minio_endpoint,
                access_key=getattr(settings, 'MINIO_ACCESS_KEY', 'minioadmin'),
                secret_key=getattr(settings, 'MINIO_SECRET_KEY', 'minioadmin'),
                secure=getattr(settings, 'MINIO_SECURE', False)
            )
            # Test connection by listing buckets
            list(minio_client.list_buckets())
            minio_status = "healthy"
    except Exception:
        minio_status = "unavailable"
    
    overall_status = "healthy" if all(
        s in ["healthy", None] or s == "unavailable" 
        for s in [db_status, redis_status, minio_status]
    ) and db_status == "healthy" else "degraded"
    
    return {
        "status": overall_status,
        "overall": overall_status,
        "database": db_status,
        "postgres": db_status,
        "redis": redis_status,
        "minio": minio_status,
        "version": "2.5.0",
    }
