"""Advanced Campaign Management Engine.

Supports 5 distinct campaign types:
1. B2B_PROSPECTING
2. NEWSLETTER
3. NURTURE
4. RE_ENGAGEMENT
5. INBOUND_FOLLOWUP

Handles audience segmentation, ICP filters, exclusion filters, member enrollment,
and campaign lifecycle controls.
"""

from typing import Dict, Any, List, Optional
import json
import uuid
import logging
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.outreach import OutreachCampaign
from app.models.campaign import CampaignMember, CampaignEvent
from app.models.business_lead import BusinessLead
from app.models.crm import Contact, Company
from app.services.compliance_service import ComplianceService
from app.services.deliverability_service import DeliverabilityService

logger = logging.getLogger(__name__)


class CampaignEngineService:
    """Manages distinct campaign types, member lifecycles, and audience segmentation."""

    CAMPAIGN_TYPES = [
        "B2B_PROSPECTING",
        "NEWSLETTER",
        "NURTURE",
        "RE_ENGAGEMENT",
        "INBOUND_FOLLOWUP",
    ]

    @classmethod
    def list_campaigns(cls, db: Session, campaign_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List campaigns with member counts and performance metrics."""
        q = db.query(OutreachCampaign)
        if campaign_type:
            q = q.filter(OutreachCampaign.channel == campaign_type)
        camps = q.order_by(OutreachCampaign.created_at.desc()).all()

        results = []
        for c in camps:
            total_members = db.query(CampaignMember).filter(CampaignMember.campaign_id == c.id).count()
            active_members = db.query(CampaignMember).filter(
                CampaignMember.campaign_id == c.id,
                CampaignMember.status.in_(["ENROLLED", "IN_PROGRESS"]),
            ).count()
            results.append({
                "id": str(c.id),
                "name": c.name,
                "description": c.description,
                "campaign_type": getattr(c, "campaign_type", "B2B_PROSPECTING") or "B2B_PROSPECTING",
                "channel": c.channel,
                "status": c.status,
                "total_members": total_members,
                "active_members": active_members,
                "sent_count": c.sent_count,
                "delivered_count": c.delivered_count,
                "replied_count": c.replied_count,
                "bounced_count": c.bounced_count,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            })
        return results

    @classmethod
    def create_campaign(cls, data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Create a new campaign with explicit campaign_type and segmentation filters."""
        camp_type = data.get("campaign_type", "B2B_PROSPECTING").upper()
        if camp_type not in cls.CAMPAIGN_TYPES:
            raise ValueError(f"Invalid campaign_type. Must be one of: {cls.CAMPAIGN_TYPES}")

        camp = OutreachCampaign(
            name=data.get("name", f"{camp_type.title()} Campaign"),
            description=data.get("description", ""),
            channel=data.get("channel", "EMAIL"),
            status="DRAFT",
            target_audience_filters=json.dumps(data.get("filters", {})),
        )
        if hasattr(camp, "campaign_type"):
            camp.campaign_type = camp_type

        db.add(camp)
        db.commit()
        db.refresh(camp)

        # Log event
        ev = CampaignEvent(
            campaign_id=camp.id,
            event_type="CAMPAIGN_CREATED",
            description=f"Campaign '{camp.name}' created with type {camp_type}.",
        )
        db.add(ev)
        db.commit()

        return {
            "id": str(camp.id),
            "name": camp.name,
            "campaign_type": camp_type,
            "status": camp.status,
        }

    @classmethod
    def enroll_prospects(
        cls,
        campaign_id: str,
        prospect_emails: List[str],
        db: Session,
    ) -> Dict[str, Any]:
        """
        Enrolls a list of prospective recipients into a campaign,
        verifying compliance eligibility and duplicate send protections.
        """
        cid = uuid.UUID(str(campaign_id))
        camp = db.query(OutreachCampaign).filter(OutreachCampaign.id == cid).first()
        if not camp:
            raise ValueError(f"Campaign '{campaign_id}' not found")

        enrolled_count = 0
        skipped_count = 0
        skip_reasons = []

        for email in prospect_emails:
            clean_email = email.lower().strip()
            if not clean_email or "@" not in clean_email:
                continue

            # 1. Compliance pre-flight check
            eligibility = ComplianceService.check_recipient_eligibility(
                recipient=clean_email,
                channel="EMAIL",
                db=db,
            )
            if not eligibility.get("is_eligible"):
                skipped_count += 1
                skip_reasons.append(f"{clean_email}: {eligibility.get('reason')}")
                continue

            # 2. Duplicate send protection
            if DeliverabilityService.check_duplicate_send(clean_email, str(cid), db):
                skipped_count += 1
                skip_reasons.append(f"{clean_email}: DUPLICATE_SEND_PREVENTED")
                continue

            # 3. Check existing enrollment in this campaign
            existing = db.query(CampaignMember).filter(
                CampaignMember.campaign_id == cid,
                CampaignMember.recipient_email == clean_email,
            ).first()
            if existing:
                skipped_count += 1
                continue

            member = CampaignMember(
                campaign_id=cid,
                recipient_email=clean_email,
                status="ENROLLED",
                current_step_number=0,
                next_step_due_at=datetime.utcnow(),
            )
            db.add(member)
            enrolled_count += 1

        camp.total_prospects += enrolled_count
        db.commit()

        return {
            "campaign_id": str(cid),
            "enrolled": enrolled_count,
            "skipped": skipped_count,
            "skip_reasons": skip_reasons[:10],
        }

    @classmethod
    def set_campaign_status(cls, campaign_id: str, new_status: str, db: Session) -> Dict[str, Any]:
        """Pause, activate, or complete a campaign."""
        cid = uuid.UUID(str(campaign_id))
        camp = db.query(OutreachCampaign).filter(OutreachCampaign.id == cid).first()
        if not camp:
            raise ValueError(f"Campaign '{campaign_id}' not found")

        old_status = camp.status
        camp.status = new_status.upper()
        
        ev = CampaignEvent(
            campaign_id=cid,
            event_type="STATUS_CHANGED",
            description=f"Status changed from {old_status} to {camp.status}.",
        )
        db.add(ev)
        db.commit()

        return {"id": str(cid), "old_status": old_status, "new_status": camp.status}
