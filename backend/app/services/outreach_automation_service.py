"""Automatic enrollment of qualified leads into outreach sequences."""

import logging
import uuid
from typing import Dict, Any, List
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.business_lead import BusinessLead
from app.models.lead_contact import LeadContact, ContactType
from app.models.campaign import FollowupSequence, CampaignMember
from app.models.outreach import OutreachCampaign

logger = logging.getLogger(__name__)


class OutreachAutomationService:
    """Handles automatic enrollment of leads into outreach sequences."""
    
    @classmethod
    def auto_enroll_in_sequence(
        cls,
        lead_id: str,
        sequence_name: str = "B2B_PROSPECTING",
        db: Session = None
    ) -> Dict[str, Any]:
        """
        Automatically enroll a qualified lead in an outreach sequence.
        
        Steps:
        1. Verify lead has valid email
        2. Check not already enrolled
        3. Get sequence by campaign_type
        4. Create CampaignMember enrollment
        5. Trigger sequence step evaluation
        """
        lead = db.query(BusinessLead).filter(BusinessLead.id == uuid.UUID(str(lead_id))).first()
        if not lead:
            return {"success": False, "error": "Lead not found"}
        
        # Check if already enrolled
        if lead.outreach_enrolled:
            return {"success": False, "error": "Lead already enrolled in outreach"}
        
        # Get lead email
        email_contact = db.query(LeadContact).filter(
            LeadContact.lead_id == lead.id,
            LeadContact.contact_type == ContactType.EMAIL
        ).first()
        
        if not email_contact:
            return {"success": False, "error": "Lead has no email address"}
        
        recipient_email = email_contact.normalized_value or email_contact.original_value
        
        # Get sequence by campaign_type
        sequence = db.query(FollowupSequence).filter(
            FollowupSequence.campaign_type == sequence_name,
            FollowupSequence.is_active == True
        ).first()
        
        if not sequence:
            return {"success": False, "error": f"Sequence '{sequence_name}' not found"}
        
        # Create or get campaign for this sequence
        campaign = db.query(OutreachCampaign).filter(
            OutreachCampaign.name == f"Auto-Enrollment: {sequence.name}"
        ).first()
        
        if not campaign:
            campaign = OutreachCampaign(
                name=f"Auto-Enrollment: {sequence.name}",
                description=f"Automated enrollment campaign for {sequence_name}",
                channel="EMAIL",
                status="ACTIVE"
            )
            db.add(campaign)
            db.flush()
        
        # Check if already member
        existing_member = db.query(CampaignMember).filter(
            CampaignMember.lead_id == lead.id,
            CampaignMember.recipient_email == recipient_email,
            CampaignMember.status.in_(["ENROLLED", "IN_PROGRESS"])
        ).first()
        
        if existing_member:
            return {"success": False, "error": "Lead already enrolled as campaign member"}
        
        # Enroll as campaign member
        member = CampaignMember(
            campaign_id=campaign.id,
            lead_id=lead.id,
            recipient_email=recipient_email,
            status="ENROLLED",
            current_step_number=0,
            next_step_due_at=datetime.utcnow(),  # First step due immediately
            enrolled_at=datetime.utcnow()
        )
        db.add(member)
        
        # Update lead status
        lead.outreach_enrolled = True
        lead.outreach_enrollment_date = datetime.utcnow()
        lead.status = "in_sequence"
        
        db.commit()
        
        # Log activity
        from app.models.crm import Activity
        activity = Activity(
            activity_type="SYSTEM",
            title=f"Auto-enrolled '{lead.business_name}' in {sequence.name}",
            description=f"Lead automatically enrolled in outreach sequence. Recipient: {recipient_email}",
            lead_id=lead.id
        )
        db.add(activity)
        db.commit()
        
        return {
            "success": True,
            "lead_id": str(lead.id),
            "sequence_name": sequence.name,
            "campaign_id": str(campaign.id),
            "member_id": str(member.id),
            "recipient_email": recipient_email
        }
    
    @classmethod
    def bulk_enroll_in_sequence(cls, lead_ids: List[str], db: Session) -> Dict[str, Any]:
        """Enroll multiple leads in outreach sequence."""
        results = {"enrolled": 0, "failed": 0, "skipped": 0, "errors": []}
        
        for lead_id in lead_ids:
            result = cls.auto_enroll_in_sequence(lead_id, db=db)
            if result.get("success"):
                results["enrolled"] += 1
            elif "already enrolled" in result.get("error", "").lower():
                results["skipped"] += 1
            else:
                results["failed"] += 1
                results["errors"].append({
                    "lead_id": lead_id,
                    "error": result.get("error")
                })
        
        return results
