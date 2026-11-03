"""FastAPI Router for Email Deliverability, Mailbox Health, and Domain Authentication."""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_api_key
from app.services.deliverability_service import DeliverabilityService

router = APIRouter(prefix="/deliverability", tags=["Email Deliverability & Mailbox Health"], dependencies=[Depends(verify_api_key)])


@router.get("/stats")
def get_deliverability_stats(db: Session = Depends(get_db)):
    """Get overall email deliverability statistics and kill switch status."""
    return DeliverabilityService.get_deliverability_stats(db=db)


@router.get("/mailboxes")
def list_mailboxes(db: Session = Depends(get_db)):
    """List connected email mailboxes, sending quotas, and health status."""
    return DeliverabilityService.list_mailboxes(db=db)


@router.get("/domains")
def list_domains(db: Session = Depends(get_db)):
    """List tracked email domains and DNS records."""
    return DeliverabilityService.list_domains(db=db)


@router.post("/domains/verify")
def verify_domain_dns(payload: Dict[str, Any] = Body(...), db: Session = Depends(get_db)):
    """Run live DNS resolution for SPF, DKIM, DMARC, and MX records."""
    domain_name = payload.get("domain_name")
    if not domain_name:
        raise HTTPException(status_code=400, detail="domain_name is required")
    return DeliverabilityService.verify_domain_dns(domain_name=domain_name, db=db)


@router.get("/kill-switch")
def get_kill_switch_status():
    """Check if the global outbound kill switch is active."""
    return {"kill_switch_active": DeliverabilityService.get_kill_switch_status()}


@router.post("/kill-switch")
def toggle_kill_switch(payload: Dict[str, Any] = Body(...), db: Session = Depends(get_db)):
    """Engage or disengage the global outbound kill switch."""
    enabled = payload.get("enabled", False)
    reason = payload.get("reason", "Operator manual override")
    return DeliverabilityService.set_kill_switch(enabled=enabled, reason=reason, db=db)
