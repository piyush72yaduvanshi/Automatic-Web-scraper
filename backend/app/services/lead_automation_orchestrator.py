"""Master orchestration service coordinating all automation steps."""

import logging
from typing import Dict, Any, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_
import uuid
from app.models.business_lead import BusinessLead
from app.services.automation_settings_service import AutomationSettingsService
from app.services.email_enrichment_service import EmailEnrichmentService
from app.services.outreach_automation_service import OutreachAutomationService
from app.services.crm_automation_service import CRMAutomationService
from app.services.lead_qualification_service import LeadQualificationService

logger = logging.getLogger(__name__)


class LeadAutomationOrchestrator:
    """Coordinates end-to-end lead automation pipeline."""
    
    @classmethod
    async def process_single_lead(cls, lead_id: str, db: Session) -> Dict[str, Any]:
        """
        Execute complete automation pipeline for one lead:
        1. Check if already processed
        2. Enrich email if missing
        3. Qualify lead if not qualified
        4. Auto-enroll in outreach if score >= threshold
        5. Auto-convert to CRM if score >= threshold
        """
        result = {
            "lead_id": lead_id,
            "steps": {
                "email_enrichment": None,
                "qualification": None,
                "outreach_enrollment": None,
                "crm_conversion": None
            },
            "success": False,
            "error": None
        }
        
        try:
            lead = db.query(BusinessLead).filter(BusinessLead.id == uuid.UUID(str(lead_id))).first()
            if not lead:
                result["error"] = "Lead not found"
                return result
            
            # Check automation settings
            auto_enroll_enabled = AutomationSettingsService.is_auto_enroll_enabled(db)
            auto_crm_enabled = AutomationSettingsService.is_auto_crm_enabled(db)
            email_enrichment_enabled = AutomationSettingsService.is_email_enrichment_enabled(db)
            min_score_outreach = AutomationSettingsService.get_min_score_for_outreach(db)
            min_score_crm = AutomationSettingsService.get_min_score_for_crm(db)
            
            # Step 1: Email enrichment (if missing)
            if email_enrichment_enabled and lead.email_enrichment_status in ['pending', 'failed', None]:
                email_result = await EmailEnrichmentService.enrich_lead_email(lead_id, db)
                result["steps"]["email_enrichment"] = email_result
            else:
                result["steps"]["email_enrichment"] = {"skipped": True, "reason": "Email already exists or enrichment disabled"}
            
            # Step 2: Qualification (if not qualified)
            if not lead.qualification_score or lead.qualification_status == "New":
                qual_result = await LeadQualificationService.qualify_lead(lead_id, db)
                result["steps"]["qualification"] = {
                    "score": qual_result.get("score"),
                    "status": qual_result.get("status")
                }
            else:
                result["steps"]["qualification"] = {
                    "skipped": True,
                    "score": lead.qualification_score,
                    "status": lead.qualification_status
                }
            
            # Refresh lead to get updated qualification
            db.refresh(lead)
            
            # Step 3: Auto-enroll in outreach (if qualified and has email)
            if auto_enroll_enabled and lead.qualification_score and lead.qualification_score >= min_score_outreach and not lead.outreach_enrolled:
                enroll_result = OutreachAutomationService.auto_enroll_in_sequence(lead_id, db=db)
                result["steps"]["outreach_enrollment"] = enroll_result
            else:
                result["steps"]["outreach_enrollment"] = {
                    "skipped": True,
                    "reason": f"Score {lead.qualification_score} < {min_score_outreach} or already enrolled or disabled"
                }
            
            # Step 4: Auto-convert to CRM (if qualified)
            if auto_crm_enabled and lead.qualification_score and lead.qualification_score >= min_score_crm and not lead.crm_converted:
                crm_result = CRMAutomationService.auto_convert_lead_to_crm(lead_id, db)
                result["steps"]["crm_conversion"] = crm_result
            else:
                result["steps"]["crm_conversion"] = {
                    "skipped": True,
                    "reason": f"Score {lead.qualification_score} < {min_score_crm} or already converted or disabled"
                }
            
            # Update last automation run
            lead.last_automation_run = datetime.utcnow()
            db.commit()
            
            result["success"] = True
            
        except Exception as e:
            logger.error(f"Error processing lead {lead_id}: {e}", exc_info=True)
            result["error"] = str(e)
        
        return result
    
    @classmethod
    async def bulk_process_leads(
        cls,
        filters: Dict[str, Any],
        batch_size: int,
        db: Session
    ) -> Dict[str, Any]:
        """
        Process multiple leads in batch with filters.
        
        Filters:
        - status: "enriched", "discovered", etc.
        - qualification_status: "New", "Qualified", etc.
        - min_score, max_score
        - has_email: bool
        """
        # Build query
        query = db.query(BusinessLead)
        
        if filters.get("status"):
            query = query.filter(BusinessLead.status == filters["status"])
        
        if filters.get("qualification_status"):
            query = query.filter(BusinessLead.qualification_status != "Disqualified")
        
        if filters.get("min_score"):
            query = query.filter(BusinessLead.qualification_score >= filters["min_score"])
        
        # Exclude already processed (unless filter says otherwise)
        if not filters.get("include_processed"):
            query = query.filter(
                and_(
                    BusinessLead.outreach_enrolled == False,
                    BusinessLead.crm_converted == False
                )
            )
        
        leads = query.limit(batch_size).all()
        
        results = {
            "processed": 0,
            "succeeded": 0,
            "failed": 0,
            "email_enriched": 0,
            "qualified": 0,
            "enrolled": 0,
            "converted": 0,
            "errors": []
        }
        
        for lead in leads:
            lead_result = await cls.process_single_lead(str(lead.id), db)
            results["processed"] += 1
            
            if lead_result.get("success"):
                results["succeeded"] += 1
                
                if lead_result["steps"]["email_enrichment"] and lead_result["steps"]["email_enrichment"].get("success"):
                    results["email_enriched"] += 1
                
                if lead_result["steps"]["qualification"] and not lead_result["steps"]["qualification"].get("skipped"):
                    results["qualified"] += 1
                
                if lead_result["steps"]["outreach_enrollment"] and lead_result["steps"]["outreach_enrollment"].get("success"):
                    results["enrolled"] += 1
                
                if lead_result["steps"]["crm_conversion"] and lead_result["steps"]["crm_conversion"].get("success"):
                    results["converted"] += 1
            else:
                results["failed"] += 1
                results["errors"].append({
                    "lead_id": str(lead.id),
                    "error": lead_result.get("error")
                })
        
        return results
