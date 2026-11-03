"""FastAPI Router for Global Consent, Marketing Eligibility, and GDPR Compliance."""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_api_key
from app.services.compliance_service import ComplianceService

router = APIRouter(prefix="/compliance", tags=["Compliance & Global Consent"], dependencies=[Depends(verify_api_key)])


@router.get("/consents")
def list_consents(limit: int = Query(50, ge=1, le=200), db: Session = Depends(get_db)):
    """List consent and lawful basis audit records."""
    return ComplianceService.list_consents(db=db, limit=limit)


@router.post("/consents")
def record_consent(data: Dict[str, Any] = Body(...), db: Session = Depends(get_db)):
    """Record or update consent details for an email or phone number."""
    try:
        return ComplianceService.record_consent(data=data, db=db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/check")
def check_recipient_eligibility(payload: Dict[str, Any] = Body(...), db: Session = Depends(get_db)):
    """
    Mandatory pre-flight compliance check:
    Verifies suppression status, kill switch, deletion requests, and channel consent.
    """
    recipient = payload.get("recipient")
    channel = payload.get("channel", "EMAIL")
    if not recipient:
        raise HTTPException(status_code=400, detail="recipient is required")
    return ComplianceService.check_recipient_eligibility(recipient=recipient, channel=channel, db=db)


@router.post("/deletion-request")
def execute_deletion_request(payload: Dict[str, Any] = Body(...), db: Session = Depends(get_db)):
    """Executes GDPR / CCPA 'Right to be Forgotten' data erasure and permanent suppression."""
    recipient = payload.get("recipient")
    reason = payload.get("reason", "USER_REQUEST")
    if not recipient:
        raise HTTPException(status_code=400, detail="recipient is required")
    try:
        return ComplianceService.execute_deletion_request(recipient=recipient, reason=reason, db=db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
