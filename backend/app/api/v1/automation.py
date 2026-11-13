"""Automation configuration and control API."""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, Body, HTTPException, Query
from sqlalchemy.orm import Session
import uuid

from app.core.database import get_db
from app.core.security import verify_api_key
from app.services.automation_settings_service import AutomationSettingsService
from app.models.automation import AutomationSettings, LeadException

router = APIRouter(prefix="/automation", tags=["Automation"], dependencies=[Depends(verify_api_key)])


@router.get("/settings")
def get_automation_settings(db: Session = Depends(get_db)):
    """Get all automation configuration settings."""
    settings = db.query(AutomationSettings).all()
    return {
        "settings": [
            {
                "key": s.setting_key,
                "value": s.setting_value,
                "type": s.data_type,
                "description": s.description,
                "updated_at": s.updated_at.isoformat() if s.updated_at else None
            }
            for s in settings
        ]
    }


@router.put("/settings/{setting_key}")
def update_automation_setting(
    setting_key: str,
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """Update a single automation setting."""
    setting = db.query(AutomationSettings).filter(AutomationSettings.setting_key == setting_key).first()
    if not setting:
        raise HTTPException(status_code=404, detail=f"Setting '{setting_key}' not found")
    
    new_value = payload.get("value")
    if new_value is None:
        raise HTTPException(status_code=400, detail="Value is required")
    
    # Type validation
    if setting.data_type == "boolean":
        if not isinstance(new_value, bool):
            raise HTTPException(status_code=400, detail="Value must be boolean")
        setting.setting_value = "true" if new_value else "false"
    elif setting.data_type == "integer":
        if not isinstance(new_value, int):
            raise HTTPException(status_code=400, detail="Value must be integer")
        setting.setting_value = str(new_value)
    else:
        setting.setting_value = str(new_value)
    
    from datetime import datetime
    setting.updated_at = datetime.utcnow()
    db.commit()
    
    return {"success": True, "setting_key": setting_key, "new_value": setting.setting_value}


@router.get("/status")
def get_automation_status(db: Session = Depends(get_db)):
    """Get current automation status summary."""
    return {
        "auto_enroll_enabled": AutomationSettingsService.is_auto_enroll_enabled(db),
        "auto_approve_enabled": AutomationSettingsService.is_auto_approve_enabled(db),
        "auto_crm_enabled": AutomationSettingsService.is_auto_crm_enabled(db),
        "min_score_outreach": AutomationSettingsService.get_min_score_for_outreach(db),
        "min_score_crm": AutomationSettingsService.get_min_score_for_crm(db)
    }


@router.get("/exceptions")
def list_exceptions(
    severity: Optional[str] = None,
    resolved: Optional[bool] = None,
    limit: int = Query(50, le=500),
    db: Session = Depends(get_db)
):
    """List automation exceptions for manual review."""
    from sqlalchemy import desc
    
    query = db.query(LeadException)
    
    if severity:
        query = query.filter(LeadException.severity == severity)
    
    if resolved is not None:
        query = query.filter(LeadException.resolved == resolved)
    
    exceptions = query.order_by(desc(LeadException.created_at)).limit(limit).all()
    
    return {
        "exceptions": [
            {
                "id": str(e.id),
                "lead_id": str(e.lead_id) if e.lead_id else None,
                "type": e.exception_type,
                "reason": e.reason,
                "severity": e.severity,
                "resolved": e.resolved,
                "created_at": e.created_at.isoformat() if e.created_at else None
            }
            for e in exceptions
        ],
        "total": len(exceptions)
    }


@router.patch("/exceptions/{exception_id}/resolve")
def resolve_exception(
    exception_id: str,
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """Mark an exception as resolved."""
    from datetime import datetime
    
    exception = db.query(LeadException).filter(LeadException.id == uuid.UUID(exception_id)).first()
    if not exception:
        raise HTTPException(status_code=404, detail="Exception not found")
    
    exception.resolved = True
    exception.resolved_at = datetime.utcnow()
    exception.resolution_notes = payload.get("notes", "Manually resolved")
    db.commit()
    
    return {"success": True, "exception_id": exception_id}
