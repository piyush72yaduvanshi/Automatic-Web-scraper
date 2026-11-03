"""FastAPI Router for Social Media & Content Marketing Engine."""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_api_key
from app.services.content_marketing_service import ContentMarketingService

router = APIRouter(prefix="/content", tags=["Content & Social Marketing"], dependencies=[Depends(verify_api_key)])


@router.get("/items")
def list_content_items(pillar: Optional[str] = None, db: Session = Depends(get_db)):
    """List content pieces mapped across the 5 pillars."""
    return ContentMarketingService.list_content_items(db=db, pillar=pillar)


@router.post("/generate")
async def create_and_repurpose_content(data: Dict[str, Any] = Body(...), db: Session = Depends(get_db)):
    """AI drafts and repurposes a core idea across LinkedIn, X, and Reddit."""
    try:
        return await ContentMarketingService.create_and_repurpose_content(data=data, db=db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/calendar")
def list_calendar_entries(db: Session = Depends(get_db)):
    """List scheduled publishing calendar entries."""
    return ContentMarketingService.list_calendar_entries(db=db)


@router.post("/calendar")
def schedule_calendar_entry(data: Dict[str, Any] = Body(...), db: Session = Depends(get_db)):
    """Schedule an approved content item onto the calendar."""
    try:
        return ContentMarketingService.schedule_calendar_entry(data=data, db=db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

