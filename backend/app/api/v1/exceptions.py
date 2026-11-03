"""FastAPI Router for Centralized Exception Queue."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_api_key
from app.services.exception_queue_service import ExceptionQueueService

router = APIRouter(prefix="/exceptions", tags=["Exception Queue"], dependencies=[Depends(verify_api_key)])


@router.get("")
def get_exception_queue(limit: int = Query(50, ge=1, le=100), db: Session = Depends(get_db)):
    """Retrieve triaged operational anomalies requiring human attention."""
    return ExceptionQueueService.get_exception_items(db=db, limit=limit)
