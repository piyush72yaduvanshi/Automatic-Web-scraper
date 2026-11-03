"""FastAPI Router for Advanced Campaign Management Engine."""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_api_key
from app.services.campaign_engine_service import CampaignEngineService

router = APIRouter(prefix="/campaigns", tags=["Campaign Management"], dependencies=[Depends(verify_api_key)])


@router.get("")
def list_campaigns(campaign_type: Optional[str] = None, db: Session = Depends(get_db)):
    """List campaigns across the 5 campaign types."""
    return CampaignEngineService.list_campaigns(db=db, campaign_type=campaign_type)


@router.post("")
def create_campaign(data: Dict[str, Any] = Body(...), db: Session = Depends(get_db)):
    """Create a new campaign with explicit type and segmentation filters."""
    try:
        return CampaignEngineService.create_campaign(data=data, db=db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{campaign_id}/enroll")
def enroll_prospects(
    campaign_id: str,
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
):
    """Enroll prospects into a campaign with pre-flight compliance & deduplication checks."""
    emails = payload.get("emails", [])
    if not emails:
        raise HTTPException(status_code=400, detail="List of 'emails' is required")
    try:
        return CampaignEngineService.enroll_prospects(campaign_id=campaign_id, prospect_emails=emails, db=db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{campaign_id}/status")
def set_campaign_status(
    campaign_id: str,
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
):
    """Update campaign status (ACTIVE, PAUSED, COMPLETED)."""
    new_status = payload.get("status")
    if not new_status:
        raise HTTPException(status_code=400, detail="'status' is required")
    try:
        return CampaignEngineService.set_campaign_status(campaign_id=campaign_id, new_status=new_status, db=db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
