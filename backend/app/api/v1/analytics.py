"""API endpoints for Analytics and KPI Reporting."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.core.database import get_db
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview")
def get_overview_analytics(db: Session = Depends(get_db)):
    """Comprehensive KPIs computed directly from leads, CRM deals, and outreach records."""
    return AnalyticsService.get_dashboard_overview(db)


@router.get("/pipeline")
def get_pipeline_analytics(db: Session = Depends(get_db)):
    """Pipeline and conversion metrics."""
    overview = AnalyticsService.get_dashboard_overview(db)
    return overview["pipeline"]


@router.get("/leads")
def get_leads_analytics(db: Session = Depends(get_db)):
    """Lead discovery, qualification, and channel availability metrics."""
    overview = AnalyticsService.get_dashboard_overview(db)
    return overview["leads"]
