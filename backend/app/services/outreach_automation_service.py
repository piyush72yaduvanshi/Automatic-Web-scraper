"""Automatic enrollment of qualified leads into outreach sequences."""

import logging
import uuid
from typing import Dict, Any, List
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.business_lead import BusinessLead
from app.models.lead_contact import LeadContact, ContactType
from app.models.campaign import FollowupSequence, CampaignMember
from app.models.outreach import OutreachCampaign, OutreachApproval

logger = logging.getLogger(__name__)


class OutreachAutomationService:
    """Handles automatic enrollment of leads into outreach sequences."""
    
    @staticmethod
    def _is_email_approvable(subject: str, body: str, recipient: str, company_name: str = "") -> bool:
        """
        Validate email meets quality standards for auto-approval.
        
        Safety checks:
        1. Subject line exists and is not empty
        2. No template placeholders ({{ }})
        3. Body has minimum length (>100 chars)
        4. Valid recipient email (not test/example domains)
        5. Basic personalization present
        """
        # Check subject line
        if not subject or len(subject.strip()) < 5:
            logger.warning(f"Auto-approval failed: subject too short or empty")
            return False
        
        # Check for template placeholders
        if '{{' in subject or '{{' in body:
            logger.warning(f"Auto-approval failed: unpersonalized template placeholders found")
            return False
        
        # Check body length
        if not body or len(body.strip()) < 100:
            logger.warning(f"Auto-approval failed: body too short ({len(body)} chars)")
            return False
        
        # Check recipient email validity
        if not recipient or '@' not in recipient:
            logger.warning(f"Auto-approval failed: invalid recipient email")
            return False
        
        # Check for test/example domains
        test_domains = ['@example.com', '@test.com', '@localhost', '@domain.com']
        if any(domain in recipient.lower() for domain in test_domains):
            logger.warning(f"Auto-approval failed: test/example domain in recipient")
            return False
        
        # Check for basic personalization (company name or substantive content)
        if company_name and company_name.lower() not in body.lower():
            # If company name provided but not in body, it might lack personalization
            # This is a soft check - we'll allow it but log a warning
            logger.info(f"Note: company name not found in body, but allowing auto-approval")
        
        return True
    
    @classmethod
    async def auto_approve_outreach_draft(
        cls,
        approval_id: str,
        db: Session
    ) -> Dict[str, Any]:
        """
        Automatically approve and send an outreach draft if it passes validation.
        If validation fails, keep it in PENDING for manual review.
        """
        from app.services.automation_settings_service import AutomationSettingsService
        from app.services.outreach_service import OutreachService
        
        # Check if auto-approval is enabled
        if not AutomationSettingsService.is_auto_approve_enabled(db):
            return {
                "success": False,
                "action": "auto_approval_disabled",
                "message": "Auto-approval is disabled in settings"
            }
        
        approval = db.query(OutreachApproval).filter(
            OutreachApproval.id == uuid.UUID(str(approval_id))
        ).first()
        
        if not approval:
            return {"success": False, "error": "Approval record not found"}
        
        if approval.status != "PENDING":
            return {"success": False, "error": f"Approval already {approval.status}"}
        
        # Get company name for personalization check
        company_name = ""
        if approval.lead_id:
            lead = db.query(BusinessLead).filter(BusinessLead.id == approval.lead_id).first()
            if lead:
                company_name = lead.business_name
        
        # Validate content
        is_valid = cls._is_email_approvable(
            subject=approval.subject or "",
            body=approval.body_content or "",
            recipient=approval.recipient_destination or "",
            company_name=company_name
        )
        
        if is_valid:
            # Auto-approve and send
            logger.info(f"Auto-approving outreach {approval_id} after validation passed")
            send_result = await OutreachService.approve_and_send(approval_id, db)
            
            return {
                "success": True,
                "action": "auto_approved",
                "approval_id": approval_id,
                "send_result": send_result
            }
        else:
            # Keep in pending for manual review
            approval.rejection_reason = "Auto-approval validation failed - requires manual review"
            db.commit()
            
            # Log exception
            from app.models.automation import LeadException
            exception = LeadException(
                lead_id=approval.lead_id,
                exception_type="EMAIL_VALIDATION_FAILED",
                reason="Email validation failed during auto-approval: content quality checks did not pass",
                severity="warning"
            )
            db.add(exception)
            db.commit()
            
            logger.warning(f"Auto-approval validation failed for {approval_id}, flagged for manual review")
            
            return {
                "success": False,
                "action": "requires_manual_review",
                "reason": "Validation failed",
                "approval_id": approval_id
            }
    
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
            "sequence_id": str(sequence.id),
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
