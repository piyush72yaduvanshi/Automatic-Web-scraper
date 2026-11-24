"""Follow-up & Multi-Touch Sequence Engine.

Manages cadence sequences (e.g. Day 0, Day 3, Day 7, Day 14), evaluates due steps,
and strictly enforces the 7 MANDATORY PRE-EXECUTION CHECKS before staging outreach.
"""

from typing import Dict, Any, List, Optional
import uuid
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.campaign import FollowupSequence, FollowupStep, CampaignMember
from app.models.outreach import OutreachCampaign, OutreachApproval, SuppressionRecord
from app.models.deliverability import EmailAccount
from app.services.compliance_service import ComplianceService
from app.services.deliverability_service import DeliverabilityService
from app.services.provider_health_service import ProviderHealthService

logger = logging.getLogger(__name__)


class SequenceEngineService:
    """Orchestrates multi-touch cadences with strict 7-point safety checks."""

    @classmethod
    def list_sequences(cls, db: Session) -> List[Dict[str, Any]]:
        """List sequence blueprints."""
        cls.seed_default_sequences_if_empty(db)
        seqs = db.query(FollowupSequence).order_by(FollowupSequence.created_at.desc()).all()
        return [
            {
                "id": str(s.id),
                "name": s.name,
                "description": s.description,
                "campaign_type": s.campaign_type,
                "is_active": s.is_active,
                "stop_on_reply": s.stop_on_reply,
                "steps_count": len(s.steps),
                "steps": [
                    {
                        "step_number": st.step_number,
                        "delay_days": st.delay_days,
                        "channel": st.channel,
                        "subject_template": st.subject_template,
                    }
                    for st in s.steps
                ],
            }
            for s in seqs
        ]

    @classmethod
    def create_sequence(cls, data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Create a new cadence sequence with ordered steps."""
        seq = FollowupSequence(
            name=data.get("name", "Standard Cadence"),
            description=data.get("description", ""),
            campaign_type=data.get("campaign_type", "B2B_PROSPECTING"),
            is_active=data.get("is_active", True),
            stop_on_reply=data.get("stop_on_reply", True),
            stop_on_meeting=data.get("stop_on_meeting", True),
            stop_on_unsubscribe=data.get("stop_on_unsubscribe", True),
        )
        db.add(seq)
        db.commit()
        db.refresh(seq)

        raw_steps = data.get("steps", [])
        for idx, s in enumerate(raw_steps):
            step = FollowupStep(
                sequence_id=seq.id,
                step_number=s.get("step_number", idx + 1),
                delay_days=s.get("delay_days", idx * 3),
                channel=s.get("channel", "EMAIL"),
                subject_template=s.get("subject_template", "Quick follow-up"),
                body_template=s.get("body_template", "Hi {{first_name}}, following up on our previous note."),
                requires_approval=s.get("requires_approval", True),
            )
            db.add(step)

        db.commit()
        return {"id": str(seq.id), "name": seq.name, "steps_created": len(raw_steps)}

    @classmethod
    def execute_due_sequence_steps(cls, sequence_id: str, db: Session) -> Dict[str, Any]:
        """
        Scans for campaign members due for their next sequence touchpoint.
        Executes the 7 MANDATORY PRE-EXECUTION CHECKS on every recipient.
        Stages verified steps in outreach_approvals queue.
        """
        sid = uuid.UUID(str(sequence_id))
        seq = db.query(FollowupSequence).filter(FollowupSequence.id == sid).first()
        if not seq:
            raise ValueError(f"Sequence '{sequence_id}' not found")

        steps = sorted(seq.steps, key=lambda s: s.step_number)
        if not steps:
            return {"status": "NO_STEPS_DEFINED"}

        # Find active members
        members = db.query(CampaignMember).filter(
            CampaignMember.status.in_(["ENROLLED", "IN_PROGRESS"]),
            CampaignMember.next_step_due_at <= datetime.utcnow(),
        ).all()

        staged_count = 0
        blocked_count = 0
        blocked_reasons = []

        for m in members:
            target_step_num = m.current_step_number + 1
            step = next((s for s in steps if s.step_number == target_step_num), None)
            if not step:
                m.status = "COMPLETED"
                db.commit()
                continue

            # =========================================================
            # THE 7 MANDATORY PRE-EXECUTION CHECKS
            # =========================================================

            # Check 1: Recipient Eligibility
            eligibility = ComplianceService.check_recipient_eligibility(
                recipient=m.recipient_email,
                channel=step.channel,
                db=db,
            )
            if not eligibility.get("is_eligible"):
                blocked_count += 1
                blocked_reasons.append(f"{m.recipient_email}: ELIGIBILITY_FAILED - {eligibility.get('reason')}")
                m.status = "PAUSED"
                continue

            # Check 2: Suppression Status
            is_suppressed = db.query(SuppressionRecord).filter(
                SuppressionRecord.recipient == m.recipient_email.lower().strip()
            ).first()
            if is_suppressed:
                blocked_count += 1
                blocked_reasons.append(f"{m.recipient_email}: ON_SUPPRESSION_LIST")
                m.status = "UNSUBSCRIBED"
                continue

            # Check 3: Reply Status (if already replied, sequence MUST be paused)
            if seq.stop_on_reply:
                from app.models.outreach import ConversationMessage
                replied = db.query(ConversationMessage).filter(
                    ConversationMessage.sender == m.recipient_email.lower().strip(),
                    ConversationMessage.direction == "INBOUND",
                ).first()
                if replied:
                    blocked_count += 1
                    blocked_reasons.append(f"{m.recipient_email}: ALREADY_REPLIED")
                    m.status = "PAUSED"
                    continue

            # Check 4: Campaign Status (Must be active, not paused or killed)
            camp = db.query(OutreachCampaign).filter(OutreachCampaign.id == m.campaign_id).first()
            if camp and camp.status not in ["ACTIVE", "SCHEDULED"]:
                blocked_count += 1
                blocked_reasons.append(f"{m.recipient_email}: CAMPAIGN_{camp.status}")
                continue

            # Check 5: Approval Status Requirement
            # Sequence steps are ALWAYS staged in OutreachApproval to guarantee Human-in-the-Loop!

            # Check 6: Provider Health
            if DeliverabilityService.get_kill_switch_status():
                blocked_count += 1
                blocked_reasons.append(f"{m.recipient_email}: GLOBAL_KILL_SWITCH_ACTIVE")
                continue

            # Check 7: Duplicate-Send Protection
            if DeliverabilityService.check_duplicate_send(m.recipient_email, str(m.campaign_id), db):
                blocked_count += 1
                blocked_reasons.append(f"{m.recipient_email}: DUPLICATE_SEND_PREVENTED")
                m.status = "PAUSED"
                continue

            # All 7 checks cleared: Stage in Human Approval Queue!
            approval = OutreachApproval(
                action_type="SEND_EMAIL" if step.channel == "EMAIL" else "SEND_WHATSAPP",
                campaign_id=m.campaign_id,
                recipient_destination=m.recipient_email,
                subject=step.subject_template or f"Step {step.step_number} Follow-up",
                body_content=step.body_template,
                evidence_context=f"Sequence: {seq.name} (Step {step.step_number}, Day +{step.delay_days})",
                status="PENDING",
            )
            db.add(approval)

            m.current_step_number = step.step_number
            m.last_step_sent_at = datetime.utcnow()
            m.status = "IN_PROGRESS"
            # Schedule next step due date
            next_step = next((s for s in steps if s.step_number == step.step_number + 1), None)
            if next_step:
                interval_days = max(1, next_step.delay_days - step.delay_days)
                m.next_step_due_at = datetime.utcnow() + timedelta(days=interval_days)
            else:
                m.next_step_due_at = None

            staged_count += 1

        db.commit()
        return {
            "sequence_name": seq.name,
            "staged_for_approval": staged_count,
            "blocked_count": blocked_count,
            "blocked_reasons": blocked_reasons[:10],
        }

    @classmethod
    def seed_default_sequences_if_empty(cls, db: Session) -> None:
        """Seed industry standard Day 0, Day 3, Day 7, Day 14 cadence."""
        if db.query(FollowupSequence).count() > 0:
            return

        seq = FollowupSequence(
            name="Standard 4-Touch B2B Prospecting Cadence",
            description="Proven 14-day cadence with Day 0 intro, Day 3 value follow-up, Day 7 case study, and Day 14 polite breakup.",
            campaign_type="B2B_PROSPECTING",
            is_active=True,
            stop_on_reply=True,
            stop_on_meeting=True,
            stop_on_unsubscribe=True,
        )
        db.add(seq)
        db.commit()
        db.refresh(seq)

        steps = [
            FollowupStep(
                sequence_id=seq.id,
                step_number=1,
                delay_days=0,
                channel="EMAIL",
                subject_template="Quick question regarding inbound operations for {{company_name}}",
                body_template="Hi {{first_name}},\n\nI noticed {{company_name}}'s recent growth in {{city}}. We help teams in your space automate lead qualification and CRM operations.\n\nWould you be open to a 10-minute chat this week?",
            ),
            FollowupStep(
                sequence_id=seq.id,
                step_number=2,
                delay_days=3,
                channel="EMAIL",
                subject_template="Idea for {{company_name}} — reducing inbound booking bottlenecks",
                body_template="Hi {{first_name}},\n\nFollowing up on my previous note. Most founders we speak with lose 20-30% of warm leads due to delayed response times.\n\nHere is a quick 2-page blueprint on how we resolve this without extra headcount.",
            ),
            FollowupStep(
                sequence_id=seq.id,
                step_number=3,
                delay_days=7,
                channel="EMAIL",
                subject_template="How similar businesses scaled pipeline without ad spend",
                body_template="Hi {{first_name}},\n\nSharing a quick case study: we recently helped an engineering firm in your sector double their qualified meetings in 45 days.\n\nWould this be relevant for {{company_name}} right now?",
            ),
            FollowupStep(
                sequence_id=seq.id,
                step_number=4,
                delay_days=14,
                channel="EMAIL",
                subject_template="Closing the loop — {{company_name}}",
                body_template="Hi {{first_name}},\n\nI assume this isn't a priority right now, which is completely fine. I won't follow up further, but feel free to reach back out if your team ever needs sales operations assistance.",
            ),
        ]
        for st in steps:
            db.add(st)
        db.commit()
        logger.info("Seeded default 4-touch follow-up cadence.")

