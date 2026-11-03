"""FastAPI Router for Daily, Weekly, and Monthly Operational Reporting."""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_api_key
from app.services.reporting_service import ReportingService

router = APIRouter(prefix="/reports", tags=["Operational Reports & Optimization"], dependencies=[Depends(verify_api_key)])


@router.get("")
def list_reports(report_type: Optional[str] = None, limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    """List historical report snapshots."""
    return ReportingService.list_reports(db=db, report_type=report_type, limit=limit)


@router.post("/generate")
async def generate_report(payload: Dict[str, Any] = Body(...), db: Session = Depends(get_db)):
    """
    Generate an operational report snapshot from real database metrics.
    report_type: DAILY, WEEKLY, or MONTHLY.
    """
    report_type = payload.get("report_type", "DAILY")
    try:
        return await ReportingService.generate_report(report_type=report_type, db=db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

