"""FastAPI Router for Follow-up & Multi-Touch Sequence Engine."""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_api_key
from app.services.sequence_engine_service import SequenceEngineService

router = APIRouter(prefix="/sequences", tags=["Follow-up Sequences"], dependencies=[Depends(verify_api_key)])


@router.get("")
def list_sequences(db: Session = Depends(get_db)):
    """List multi-touch cadence sequences."""
    return SequenceEngineService.list_sequences(db=db)


@router.post("")
def create_sequence(data: Dict[str, Any] = Body(...), db: Session = Depends(get_db)):
    """Create a new cadence sequence with ordered touchpoint steps."""
    try:
        return SequenceEngineService.create_sequence(data=data, db=db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{sequence_id}/execute-due")
def execute_due_sequence_steps(sequence_id: str, db: Session = Depends(get_db)):
    """
    Evaluates due touchpoints and stages them in Outreach Approvals
    after passing the 7 MANDATORY PRE-EXECUTION CHECKS.
    """
    try:
        return SequenceEngineService.execute_due_sequence_steps(sequence_id=sequence_id, db=db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
