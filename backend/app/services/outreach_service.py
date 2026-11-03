"""Outreach Service with Human-in-the-Loop Approval Queue.

Enforces:
1. Every outbound email or message MUST be explicitly approved by the human user.
2. Suppression list verification before sending (auto-blocks unsubscribes/bounces).
3. Activity timeline and conversation synchronization.
"""

from typing import Dict, Any, List, Optional
import uuid
import json
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.outreach import (
    OutreachCampaign,
    CampaignStep,
    OutreachApproval,
    Conversation,
    ConversationMessage,
    SuppressionRecord,
)
from app.models.business_lead import BusinessLead
from app.models.crm import Contact, Company, Activity
from app.providers.communication.gmail_provider import GmailProvider
from app.providers.communication.whatsapp_provider import WhatsAppProvider
from app.ai.agents.specialized import AgentRegistry

logger = logging.getLogger(__name__)


class OutreachService:
    """Manages campaigns, approval queue, suppression, and multi-channel messaging."""

    # -------------------------------------------------------------
    # Suppression & Opt-Out
    # -------------------------------------------------------------
    @classmethod
    def is_suppressed(cls, recipient: str, channel: str, db: Session) -> bool:
        """Check if recipient has opted out or bounced."""
        clean = recipient.lower().strip()
        rec = db.query(SuppressionRecord).filter(SuppressionRecord.recipient == clean).first()
        if rec and (rec.channel in ["ALL", channel.upper()]):
            return True
        return False

    @classmethod
    def add_to_suppression(
        cls,
        recipient: str,
        channel: str = "ALL",
        reason: str = "UNSUBSCRIBE",
        db: Session = None,
    ) -> SuppressionRecord:
        clean = recipient.lower().strip()
        existing = db.query(SuppressionRecord).filter(SuppressionRecord.recipient == clean).first()
        if existing:
            return existing

        suppression = SuppressionRecord(
            recipient=clean,
            channel=channel.upper(),
            reason=reason,
        )
        db.add(suppression)
        db.commit()
        db.refresh(suppression)
        return suppression

    @classmethod
    def list_suppression(cls, db: Session) -> List[SuppressionRecord]:
        return db.query(SuppressionRecord).order_by(desc(SuppressionRecord.opted_out_at)).all()

    # -------------------------------------------------------------
    # Human Approval Queue
    # -------------------------------------------------------------
    @classmethod
    def list_approvals(cls, db: Session, status: Optional[str] = None) -> List[OutreachApproval]:
        query = db.query(OutreachApproval)
        if status:
            query = query.filter(OutreachApproval.status == status)
        return query.order_by(desc(OutreachApproval.created_at)).all()

    @classmethod
    async def approve_and_send(cls, approval_id: str, db: Session) -> Dict[str, Any]:
        """Human user explicitly approves sending an outreach message."""
        approval = db.query(OutreachApproval).filter(OutreachApproval.id == uuid.UUID(str(approval_id))).first()
        if not approval:
            raise ValueError(f"Approval record not found: {approval_id}")

        if approval.status == "SENT":
            return {"success": False, "message": "Action was already executed."}

        # Check suppression
        if cls.is_suppressed(approval.recipient_destination, approval.action_type, db):
            approval.status = "REJECTED"
            approval.rejection_reason = "Recipient is on the suppression list (opted out or bounced)."
            db.commit()
            return {"success": False, "message": "Recipient is suppressed. Sending blocked."}

        # Execute communication
        send_result = {}
        if "EMAIL" in approval.action_type.upper():
            send_result = await GmailProvider.send_email(
                to_email=approval.recipient_destination,
                subject=approval.subject or "Partnership Opportunity",
                body_content=approval.body_content,
            )
        elif "WHATSAPP" in approval.action_type.upper():
            send_result = await WhatsAppProvider.send_message(
                to_phone=approval.recipient_destination,
                message_body=approval.body_content,
            )
        else:
            send_result = {"success": True, "message": f"Action '{approval.action_type}' recorded."}

        if send_result.get("success"):
            approval.status = "SENT"
            approval.sent_at = datetime.utcnow()
            approval.error_message = None

            # Log CRM activity
            act = Activity(
                activity_type="EMAIL" if "EMAIL" in approval.action_type.upper() else "CALL",
                title=f"Sent {approval.action_type} to {approval.recipient_destination}",
                description=f"Subject: {approval.subject}\n\nContent:\n{approval.body_content}",
                lead_id=approval.lead_id,
                contact_id=approval.contact_id,
            )
            db.add(act)

            # Update conversation thread
            conv = db.query(Conversation).filter(
                Conversation.subject == approval.subject,
                Conversation.channel == ("EMAIL" if "EMAIL" in approval.action_type.upper() else "WHATSAPP"),
            ).first()

            if not conv:
                conv = Conversation(
                    channel="EMAIL" if "EMAIL" in approval.action_type.upper() else "WHATSAPP",
                    subject=approval.subject,
                    contact_id=approval.contact_id,
                    status="ACTIVE",
                )
                db.add(conv)
                db.flush()

            msg = ConversationMessage(
                conversation_id=conv.id,
                direction="OUTBOUND",
                sender="me",
                recipient=approval.recipient_destination,
                subject=approval.subject,
                body=approval.body_content,
                delivery_status="sent",
            )
            db.add(msg)
            conv.last_message_at = datetime.utcnow()

            db.commit()
            return {"success": True, "approval_id": str(approval.id), "send_result": send_result}
        else:
            approval.status = "FAILED"
            approval.error_message = send_result.get("error", "Unknown sending failure")
            db.commit()
            return {"success": False, "approval_id": str(approval.id), "error": approval.error_message}

    @classmethod
    def reject_approval(cls, approval_id: str, reason: str, db: Session) -> OutreachApproval:
        approval = db.query(OutreachApproval).filter(OutreachApproval.id == uuid.UUID(str(approval_id))).first()
        if not approval:
            raise ValueError(f"Approval record not found: {approval_id}")
        approval.status = "REJECTED"
        approval.rejection_reason = reason
        db.commit()
        db.refresh(approval)
        return approval

    @classmethod
    def edit_approval(cls, approval_id: str, new_subject: Optional[str], new_body: str, db: Session) -> OutreachApproval:
        approval = db.query(OutreachApproval).filter(OutreachApproval.id == uuid.UUID(str(approval_id))).first()
        if not approval:
            raise ValueError(f"Approval record not found: {approval_id}")
        if new_subject:
            approval.subject = new_subject
        approval.body_content = new_body
        db.commit()
        db.refresh(approval)
        return approval

    # -------------------------------------------------------------
    # Automated Draft Preparation (Queued for Human Approval)
    # -------------------------------------------------------------
    @classmethod
    async def prepare_outreach_draft_for_lead(
        cls,
        lead_id: str,
        channel: str = "EMAIL",
        db: Session = None,
    ) -> OutreachApproval:
        """AI generates personalized outreach and puts it into the PENDING human approval queue."""
        lead = db.query(BusinessLead).filter(BusinessLead.id == uuid.UUID(str(lead_id))).first()
        if not lead:
            raise ValueError(f"Lead not found: {lead_id}")

        recipient_dest = None
        if channel.upper() == "EMAIL":
            email_c = next((c for c in lead.contacts if c.contact_type.value == "EMAIL"), None)
            if email_c:
                recipient_dest = email_c.normalized_value or email_c.original_value
        else:
            phone_c = next((c for c in lead.contacts if c.contact_type.value == "PHONE"), None)
            if phone_c:
                recipient_dest = phone_c.normalized_value or phone_c.original_value

        if not recipient_dest:
            recipient_dest = f"contact@{lead.website or 'company.com'}"

        # Check suppression
        if cls.is_suppressed(recipient_dest, channel, db):
            raise ValueError(f"Recipient '{recipient_dest}' is on suppression list.")

        # Invoke personalization agent
        agent = AgentRegistry.get_agent("email_personalization_agent")
        res = await agent.run(
            input_data={
                "company_name": lead.business_name,
                "contact_name": lead.business_name + " Team",
                "pain_points": ["Manual business processes", "Lead capture efficiency"],
                "offering": "AI Sales & CRM Modernization System",
                "verified_facts": [f"Category: {lead.category}", f"Location: {lead.city}"],
            },
            db=db,
        )

        subject = res.get("subject_line", f"Quick question regarding {lead.business_name}")
        body = res.get("email_body", "Hi team,\n\nI noticed your great work and wanted to reach out regarding our sales and workflow automation services.")

        approval = OutreachApproval(
            action_type="SEND_EMAIL" if channel.upper() == "EMAIL" else "SEND_WHATSAPP",
            lead_id=lead.id,
            recipient_name=f"{lead.business_name} Team",
            recipient_destination=recipient_dest,
            subject=subject,
            body_content=body,
            evidence_context=f"Lead Score: {lead.qualification_score} | Category: {lead.category} | Reason: {res.get('personalization_reason', 'Tailored cold outreach')}",
            status="PENDING",
        )
        db.add(approval)
        db.commit()
        db.refresh(approval)
        return approval

    # -------------------------------------------------------------
    # Campaigns
    # -------------------------------------------------------------
    @classmethod
    def list_campaigns(cls, db: Session) -> List[OutreachCampaign]:
        return db.query(OutreachCampaign).order_by(desc(OutreachCampaign.created_at)).all()

    @classmethod
    def create_campaign(cls, data: Dict[str, Any], db: Session) -> OutreachCampaign:
        camp = OutreachCampaign(
            name=data["name"],
            description=data.get("description"),
            channel=data.get("channel", "EMAIL"),
            status="DRAFT",
        )
        db.add(camp)
        db.flush()

        steps_data = data.get("steps", [
            {"step_number": 1, "delay_days": 0, "template_subject": "Introductory note", "template_body": "Hi,\n\nReaching out..."},
            {"step_number": 2, "delay_days": 3, "template_subject": "Following up", "template_body": "Hi,\n\nFollowing up..."},
        ])
        for s in steps_data:
            step = CampaignStep(
                campaign_id=camp.id,
                step_number=s.get("step_number", 1),
                delay_days=s.get("delay_days", 0),
                template_subject=s.get("template_subject"),
                template_body=s.get("template_body", "Template content"),
                channel=s.get("channel", camp.channel),
            )
            db.add(step)

        db.commit()
        db.refresh(camp)
        return camp

    # -------------------------------------------------------------
    # Conversations & Messages
    # -------------------------------------------------------------
    @classmethod
    def list_conversations(cls, db: Session) -> List[Conversation]:
        return db.query(Conversation).order_by(desc(Conversation.last_message_at)).all()

    @classmethod
    def get_conversation(cls, conv_id: str, db: Session) -> Optional[Conversation]:
        return db.query(Conversation).filter(Conversation.id == uuid.UUID(str(conv_id))).first()
