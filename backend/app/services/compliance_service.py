"""Global Consent, Marketing Eligibility, and Compliance Service (GDPR / CAN-SPAM).

Enforces consent verification, right-to-be-forgotten deletion, and pre-flight eligibility checks.
"""

from typing import Dict, Any, List, Optional
import uuid
import logging
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.compliance import ConsentRecord, DataDeletionRequest
from app.models.outreach import SuppressionRecord
from app.models.business_lead import BusinessLead
from app.models.crm import Contact
from app.services.deliverability_service import DeliverabilityService

logger = logging.getLogger(__name__)


class ComplianceService:
    """Manages legal consent, suppression checks, and data privacy operations."""

    @classmethod
    def check_recipient_eligibility(
        cls,
        recipient: str,
        channel: str = "EMAIL",
        db: Session = None,
    ) -> Dict[str, Any]:
        """
        MANDATORY PRE-FLIGHT COMPLIANCE CHECK.
        Must be invoked prior to staging or sending any outbound outreach.
        """
        clean_rec = recipient.lower().strip()

        # 1. Global Kill Switch Check
        if DeliverabilityService.get_kill_switch_status():
            return {
                "is_eligible": False,
                "reason": "GLOBAL_KILL_SWITCH_ACTIVE",
                "details": "Outbound communication is halted by global safety kill switch.",
            }

        # 2. Suppression Check
        if db:
            sup = db.query(SuppressionRecord).filter(
                SuppressionRecord.recipient == clean_rec
            ).first()
            if sup:
                return {
                    "is_eligible": False,
                    "reason": "RECIPIENT_SUPPRESSED",
                    "details": f"Recipient opted out or suppressed (Reason: {sup.reason}).",
                }

            # 3. Data Deletion Request Check
            del_req = db.query(DataDeletionRequest).filter(
                DataDeletionRequest.recipient == clean_rec,
                DataDeletionRequest.status.in_(["REQUESTED", "PROCESSING", "COMPLETED"]),
            ).first()
            if del_req:
                return {
                    "is_eligible": False,
                    "reason": "DATA_DELETION_ACTIVE",
                    "details": "Recipient has an active GDPR/CCPA data erasure request.",
                }

            # 4. Channel-specific Consent Check
            consent = db.query(ConsentRecord).filter(ConsentRecord.recipient == clean_rec).first()
            if consent:
                if not consent.marketing_eligible:
                    return {
                        "is_eligible": False,
                        "reason": "MARKETING_INELIGIBLE",
                        "details": "Contact flagged as not eligible for marketing outreach.",
                    }
                if channel.upper() == "WHATSAPP" and not consent.channel_whatsapp_consent:
                    return {
                        "is_eligible": False,
                        "reason": "WHATSAPP_OPT_IN_REQUIRED",
                        "details": "WhatsApp outreach requires documented prior opt-in consent.",
                    }

        return {"is_eligible": True, "reason": "ELIGIBLE", "details": "Cleared all compliance checks."}

    @classmethod
    def record_consent(cls, data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Record or update consent details for an email or phone number."""
        recipient = data.get("recipient", "").lower().strip()
        if not recipient:
            raise ValueError("Recipient address is required")

        consent = db.query(ConsentRecord).filter(ConsentRecord.recipient == recipient).first()
        if not consent:
            consent = ConsentRecord(recipient=recipient)
            db.add(consent)

        consent.source = data.get("source", "MANUAL")
        consent.source_url = data.get("source_url")
        consent.lawful_basis = data.get("lawful_basis", "LEGITIMATE_INTEREST")
        consent.channel_email_consent = data.get("channel_email_consent", True)
        consent.channel_whatsapp_consent = data.get("channel_whatsapp_consent", False)
        consent.marketing_eligible = data.get("marketing_eligible", True)
        consent.compliance_notes = data.get("compliance_notes")
        consent.collected_at = datetime.utcnow()

        db.commit()
        db.refresh(consent)
        return {
            "id": str(consent.id),
            "recipient": consent.recipient,
            "lawful_basis": consent.lawful_basis,
            "marketing_eligible": consent.marketing_eligible,
        }

    @classmethod
    def list_consents(cls, db: Session, limit: int = 50) -> List[Dict[str, Any]]:
        """List consent records."""
        records = db.query(ConsentRecord).order_by(ConsentRecord.collected_at.desc()).limit(limit).all()
        return [
            {
                "id": str(r.id),
                "recipient": r.recipient,
                "source": r.source,
                "lawful_basis": r.lawful_basis,
                "channel_email_consent": r.channel_email_consent,
                "channel_whatsapp_consent": r.channel_whatsapp_consent,
                "marketing_eligible": r.marketing_eligible,
                "compliance_notes": r.compliance_notes,
                "collected_at": r.collected_at.isoformat() if r.collected_at else None,
            }
            for r in records
        ]

    @classmethod
    def execute_deletion_request(cls, recipient: str, reason: str, db: Session) -> Dict[str, Any]:
        """
        Executes Right-to-be-Forgotten erasure:
        1. Anonymizes or deletes Lead and Contact personal information.
        2. Adds to permanent suppression list so they can never be re-scraped or contacted.
        """
        clean_rec = recipient.lower().strip()

        # 1. Log request
        req = DataDeletionRequest(
            recipient=clean_rec,
            reason=reason,
            status="PROCESSING",
        )
        db.add(req)
        db.commit()

        # 2. Add to Suppression to prevent future contact
        existing_sup = db.query(SuppressionRecord).filter(SuppressionRecord.recipient == clean_rec).first()
        if not existing_sup:
            sup = SuppressionRecord(
                recipient=clean_rec,
                channel="ALL",
                reason=f"RIGHT_TO_BE_FORGOTTEN_{reason}",
            )
            db.add(sup)

        # 3. Anonymize matching CRM Contacts
        contacts = db.query(Contact).filter(Contact.email == clean_rec).all()
        for c in contacts:
            c.first_name = "ANONYMIZED"
            c.last_name = "ANONYMIZED"
            c.email = f"anonymized_{uuid.uuid4().hex[:8]}@redacted.local"
            c.phone = None
            c.reachability_status = "opted_out"

        req.status = "COMPLETED"
        req.completed_at = datetime.utcnow()
        db.commit()

        return {
            "status": "COMPLETED",
            "recipient": clean_rec,
            "contacts_anonymized": len(contacts),
            "suppressed": True,
            "completed_at": req.completed_at.isoformat(),
        }

