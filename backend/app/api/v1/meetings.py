"""FastAPI Router for Meeting Scheduling, Calendar Integration & AI Briefings."""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_api_key
from app.services.meeting_service import MeetingService

router = APIRouter(prefix="/meetings", tags=["Meeting Management & Calendar"], dependencies=[Depends(verify_api_key)])


@router.get("")
def list_meetings(db: Session = Depends(get_db)):
    """List scheduled meetings and AI briefing dossiers."""
    return MeetingService.list_meetings(db=db)


@router.post("")
async def schedule_meeting(data: Dict[str, Any] = Body(...), db: Session = Depends(get_db)):
    """Schedule meeting, sync to calendar, and generate AI briefing dossier."""
    try:
        return await MeetingService.schedule_meeting(data=data, db=db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
