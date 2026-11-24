"""Automatic lead-to-CRM conversion without manual intervention."""

import logging
import uuid
from typing import Dict, Any, List
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.business_lead import BusinessLead
from app.services.crm_service import CRMService

logger = logging.getLogger(__name__)


class CRMAutomationService:
    """Handles automatic conversion of leads to CRM entities."""
    
    @classmethod
    def auto_convert_lead_to_crm(cls, lead_id: str, db: Session) -> Dict[str, Any]:
        """
        Automatically convert a qualified lead to CRM:
        1. Create Company from lead data
        2. Create Contact(s) from lead contacts
        3. Create Deal in "Lead" stage
        4. Update lead status to 'converted_to_crm'
        """
        lead = db.query(BusinessLead).filter(BusinessLead.id == uuid.UUID(str(lead_id))).first()
        if not lead:
            return {"success": False, "error": "Lead not found"}
        
        # Check if already converted
        if lead.crm_converted or lead.company_id:
            return {
                "success": False,
                "error": "Lead already converted to CRM",
                "company_id": str(lead.company_id) if lead.company_id else None
            }
        
        try:
            # Use existing CRMService.convert_lead_to_company method
            result = CRMService.convert_lead_to_company(db, str(lead_id))
            
            # Mark lead as converted
            lead.crm_converted = True
            lead.crm_conversion_date = datetime.utcnow()
            lead.status = "converted_to_crm"
            db.commit()
            
            # Log activity
            from app.models.crm import Activity
            activity = Activity(
                activity_type="SYSTEM",
                title=f"Auto-converted lead '{lead.business_name}' to CRM",
                description=f"Automated conversion: Company, Contact, and Deal created from lead qualification",
                lead_id=lead.id,
                company_id=result.get("company").id if result.get("company") else None
            )
            db.add(activity)
            db.commit()
            
            return {
                "success": True,
                "company_id": result.get("company_id"),
                "lead_name": lead.business_name
            }
            
        except Exception as e:
            logger.error(f"Failed to auto-convert lead {lead_id} to CRM: {e}", exc_info=True)
            
            # Log exception
            from app.models.automation import LeadException
            exception = LeadException(
                lead_id=uuid.UUID(str(lead_id)),
                exception_type="CRM_CONVERSION_FAILED",
                reason=str(e),
                severity="error"
            )
            db.add(exception)
            db.commit()
            
            return {"success": False, "error": str(e)}
    
    @classmethod
    def bulk_convert_to_crm(cls, lead_ids: List[str], db: Session) -> Dict[str, Any]:
        """Convert multiple leads to CRM in batch."""
        results = {"converted": 0, "failed": 0, "skipped": 0, "errors": []}
        
        for lead_id in lead_ids:
            result = cls.auto_convert_lead_to_crm(lead_id, db)
            if result.get("success"):
                results["converted"] += 1
            elif "already converted" in result.get("error", "").lower():
                results["skipped"] += 1
            else:
                results["failed"] += 1
                results["errors"].append({
                    "lead_id": lead_id,
                    "error": result.get("error")
                })
        
        return results
