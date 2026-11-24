"""AI Lead Qualification Engine.

Evaluates leads against configurable weighted factors:
- ICP fit (default 25%)
- Business pain (default 25%)
- Timing & intent signals (default 20%)
- Contact reachability (default 15%)
- Evidence quality (default 15%)

Generates 0-100 score, status, evidence, missing information, and next action recommendations.
Supports manual score feedback and adjustment audit logging.
"""

from typing import Dict, Any, List, Optional
import json
import logging
import uuid
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.business_lead import BusinessLead
from app.models.orchestration import AuditLog
from app.providers.ai.router import ai_router

logger = logging.getLogger(__name__)


class LeadQualificationService:
    """Intelligent lead scoring, status classification, and ICP qualification engine."""

    VALID_STATUSES = [
        "New",
        "Researching",
        "Qualified",
        "Maybe",
        "Rejected",
        "Contacted",
        "Responded",
        "Meeting Scheduled",
        "Proposal",
        "Negotiation",
        "Won",
        "Lost",
    ]

    @classmethod
    async def qualify_lead(
        cls,
        lead_id: str,
        db: Session,
        icp_profile: Optional[str] = None,
        custom_weights: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """Qualify a lead, calculate 0-100 score, determine status, and persist results."""
        lead = db.query(BusinessLead).filter(BusinessLead.id == (uuid.UUID(str(lead_id)) if isinstance(lead_id, str) else lead_id)).first()
        if not lead:
            raise ValueError(f"Lead not found: {lead_id}")

        weights = {
            "fit": (custom_weights or {}).get("fit", settings.ICP_WEIGHT_FIT),
            "pain": (custom_weights or {}).get("pain", settings.ICP_WEIGHT_PAIN),
            "timing": (custom_weights or {}).get("timing", settings.ICP_WEIGHT_TIMING),
            "reachability": (custom_weights or {}).get("reachability", settings.ICP_WEIGHT_REACHABILITY),
            "evidence": (custom_weights or {}).get("evidence", settings.ICP_WEIGHT_EVIDENCE),
        }

        # Normalize weights to sum to 1.0
        total_w = sum(weights.values()) or 1.0
        for k in weights:
            weights[k] = weights[k] / total_w

        # Gather lead context
        contacts_summary = [f"{c.contact_type.value}: {c.normalized_value or c.original_value} (status: {c.verification_status})" for c in lead.contacts]
        socials_summary = [f"{s.platform.value}: {s.profile_url}" for s in lead.social_profiles]
        evidence_summary = [f"{e.field_name}: {e.extracted_value} from {e.source_url}" for e in lead.source_evidence[:8]]

        company_context = lead.company_research or ""

        # Programmatic reachability & evidence scoring baseline
        has_verified_email = any(c.contact_type.value == "EMAIL" for c in lead.contacts)
        has_phone = any(c.contact_type.value == "PHONE" for c in lead.contacts)
        reachability_raw = 0
        if has_verified_email:
            reachability_raw += 60
        if has_phone:
            reachability_raw += 40

        evidence_raw = min(len(lead.source_evidence) * 20 + (30 if lead.website else 0), 100)

        prompt = f"""Evaluate this sales prospect and qualify against Ideal Customer Profile.
Target ICP Definition: {icp_profile or 'B2B companies or growing regional businesses needing software engineering, CRM modernization, or automated client discovery.'}

Company Name: {lead.business_name}
Category: {lead.category or 'Unknown'}
Location: {lead.city or ''}, {lead.state or ''}, {lead.country or ''}
Website: {lead.website or 'None'}
Description: {lead.description or 'None'}
Contacts Identified: {', '.join(contacts_summary) if contacts_summary else 'None'}
Social Media Profiles: {', '.join(socials_summary) if socials_summary else 'None'}
Source Evidence Trail: {', '.join(evidence_summary) if evidence_summary else 'None'}
Existing Research Dossier: {company_context[:1000]}

Configure the score using these sub-criteria (each 0 to 100):
1. 'icp_fit_score' (Weight {weights['fit']*100:.0f}%): Does this business match company size, category, and target domain?
2. 'business_pain_score' (Weight {weights['pain']*100:.0f}%): How urgently do they experience operational or technical pain?
3. 'timing_intent_score' (Weight {weights['timing']*100:.0f}%): Are there hiring signals, active expansion, or fresh listings?
4. 'reachability_score' (Weight {weights['reachability']*100:.0f}%): Reachability score (baseline is {reachability_raw})
5. 'evidence_score' (Weight {weights['evidence']*100:.0f}%): Evidence quality score (baseline is {evidence_raw})

Determine:
- 'qualification_status': One of ['Qualified', 'Maybe', 'Rejected', 'Researching']
- 'reasoning': Detailed explanation of score and status
- 'missing_information': List of critical unknown data points
- 'recommended_next_action': Concrete sales step (e.g., 'Draft email to founder', 'Search LinkedIn for Head of Sales', etc.)
"""

        schema = """{
  "icp_fit_score": 80,
  "business_pain_score": 75,
  "timing_intent_score": 60,
  "reachability_score": 85,
  "evidence_score": 70,
  "qualification_status": "Qualified",
  "reasoning": "string",
  "missing_information": ["string"],
  "recommended_next_action": "string"
}"""

        ai_out = await ai_router.generate_structured(
            prompt=prompt,
            schema_description=schema,
            system_instruction="You are an expert sales development qualification engine. Produce objective, evidence-based lead qualification assessments.",
        )

        fit_s = float(ai_out.get("icp_fit_score", 60))
        pain_s = float(ai_out.get("business_pain_score", 60))
        timing_s = float(ai_out.get("timing_intent_score", 50))
        reach_s = float(ai_out.get("reachability_score", reachability_raw))
        evid_s = float(ai_out.get("evidence_score", evidence_raw))

        composite_score = round(
            fit_s * weights["fit"] +
            pain_s * weights["pain"] +
            timing_s * weights["timing"] +
            reach_s * weights["reachability"] +
            evid_s * weights["evidence"],
            1
        )
        composite_score = max(0.0, min(100.0, composite_score))

        status = ai_out.get("qualification_status", "Qualified" if composite_score >= 70 else ("Maybe" if composite_score >= 45 else "Rejected"))
        if status not in cls.VALID_STATUSES:
            status = "Qualified" if composite_score >= 70 else "Maybe"

        breakdown = {
            "weights": weights,
            "scores": {
                "icp_fit": fit_s,
                "business_pain": pain_s,
                "timing_intent": timing_s,
                "reachability": reach_s,
                "evidence_quality": evid_s,
            },
            "composite_score": composite_score,
        }

        # Update Lead in DB
        lead.qualification_score = composite_score
        lead.qualification_status = status
        lead.qualification_reasoning = ai_out.get("reasoning", "Lead evaluated successfully.")
        lead.qualification_breakdown = json.dumps(breakdown)
        lead.data_confidence_score = evid_s
        lead.status = "qualified" if status == "Qualified" else lead.status

        db.commit()
        db.refresh(lead)

        return {
            "lead_id": str(lead.id),
            "business_name": lead.business_name,
            "qualification_score": composite_score,
            "qualification_status": status,
            "reasoning": lead.qualification_reasoning,
            "breakdown": breakdown,
            "missing_information": ai_out.get("missing_information", []),
            "recommended_next_action": ai_out.get("recommended_next_action", "Draft personalized outreach"),
        }

    @classmethod
    def apply_manual_feedback(
        cls,
        lead_id: str,
        new_score: Optional[float],
        new_status: Optional[str],
        reason: str,
        db: Session,
    ) -> Dict[str, Any]:
        """Manually override score or status with transparent audit tracking."""
        lead = db.query(BusinessLead).filter(BusinessLead.id == (uuid.UUID(str(lead_id)) if isinstance(lead_id, str) else lead_id)).first()
        if not lead:
            raise ValueError(f"Lead not found: {lead_id}")

        old_score = lead.qualification_score
        old_status = lead.qualification_status

        if new_score is not None:
            lead.qualification_score = max(0.0, min(100.0, float(new_score)))
        if new_status and new_status in cls.VALID_STATUSES:
            lead.qualification_status = new_status

        # Create audit log record
        log = AuditLog(
            action="MANUAL_SCORE_OVERRIDE",
            entity_type="business_lead",
            entity_id=str(lead.id),
            details=json.dumps({
                "old_score": old_score,
                "new_score": lead.qualification_score,
                "old_status": old_status,
                "new_status": lead.qualification_status,
                "reason": reason,
            }),
        )
        db.add(log)
        db.commit()
        db.refresh(lead)

        return {
            "lead_id": str(lead.id),
            "qualification_score": lead.qualification_score,
            "qualification_status": lead.qualification_status,
            "audit_recorded": True,
        }
