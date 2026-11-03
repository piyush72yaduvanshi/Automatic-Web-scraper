"""Reply Intelligence & Stop Conditions Engine.

Classifies incoming prospect replies across 11 intent categories, drafts suggested replies,
and enforces automated stop conditions (pauses sequences, suppresses on unsubscribe/complaint,
and creates urgent CRM tasks for interested leads).
"""

from typing import Dict, Any, List, Optional
import json
import uuid
import logging
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.outreach import Conversation, ConversationMessage, SuppressionRecord
from app.models.campaign import CampaignMember
from app.models.crm import CRMTask, Activity
from app.providers.ai.router import ai_router
from app.services.workflow_engine_service import WorkflowEngineService

logger = logging.getLogger(__name__)


class ReplyIntelligenceService:
    """Classifies inbound replies and enforces campaign stop conditions."""

    INTENT_CATEGORIES = [
        "INTERESTED",
        "REQUEST_FOR_INFO",
        "NOT_NOW",
        "REFERRAL",
        "MEETING_REQUEST",
        "OBJECTION",
        "NEGATIVE",
        "UNSUBSCRIBE",
        "OUT_OF_OFFICE",
        "COMPLAINT",
        "UNKNOWN",
    ]

    @classmethod
    async def process_incoming_message(
        cls,
        conversation_id: str,
        sender: str,
        body_text: str,
        db: Session,
    ) -> Dict[str, Any]:
        """
        Processes an incoming prospect message:
        1. Classifies reply into one of 11 categories.
        2. Applies stop conditions (pause follow-ups, suppress if opt-out).
        3. Creates CRM tasks or alerts if interested.
        4. Synthesizes an AI response proposal.
        """
        # 1. Classify with AI Provider
        classification_result = await cls.classify_reply(body_text)
        category = classification_result.get("classification", "UNKNOWN")
        sentiment = classification_result.get("sentiment", "Neutral")
        suggested_reply = classification_result.get("suggested_reply", "")
        summary = classification_result.get("summary", "")

        # 2. Persist message to conversation
        msg = ConversationMessage(
            conversation_id=uuid.UUID(str(conversation_id)),
            direction="INBOUND",
            sender=sender,
            recipient="me",
            body=body_text,
            ai_classification=category,
            suggested_reply=suggested_reply,
            delivery_status="read",
        )
        db.add(msg)

        conv = db.query(Conversation).filter(Conversation.id == uuid.UUID(str(conversation_id))).first()
        if conv:
            conv.last_message_at = datetime.utcnow()
        db.commit()

        # 3. Enforce Stop Conditions
        stop_actions = await cls._apply_stop_conditions(
            category=category,
            sender=sender,
            conversation=conv,
            body_text=body_text,
            db=db,
        )

        # 4. Emit workflow event for native Python automation bus
        await WorkflowEngineService.emit_event(
            event_type="REPLY_CLASSIFIED",
            payload={
                "sender": sender,
                "conversation_id": str(conversation_id),
                "classification": category,
                "sentiment": sentiment,
                "body_snippet": body_text[:200],
            },
            db=db,
        )

        return {
            "message_id": str(msg.id),
            "classification": category,
            "sentiment": sentiment,
            "summary": summary,
            "suggested_reply": suggested_reply,
            "stop_actions_applied": stop_actions,
        }

    @classmethod
    async def classify_reply(cls, reply_text: str) -> Dict[str, Any]:
        """Classifies raw text into 11 granular intent categories with offline heuristic fallback."""
        prompt = f"""You are a Senior Inbound Sales Intelligence Specialist.
Classify this incoming prospect response into exactly ONE of the 11 categories:
- INTERESTED: Wants a demo, pricing, trial, or conversation
- REQUEST_FOR_INFO: Asks specific technical or capability questions
- NOT_NOW: Politely deferred (busy this quarter, reach back later)
- REFERRAL: Directs to another colleague or department head
- MEETING_REQUEST: Specifically asks to book a call, sends availability, or asks for calendar link
- OBJECTION: Expresses skepticism, pricing concerns, or current provider satisfaction
- NEGATIVE: Explicit rejection without curiosity
- UNSUBSCRIBE: Requests removal, opt-out, 'unsubscribe', 'stop', 'do not contact'
- OUT_OF_OFFICE: Automated auto-reply or vacation responder
- COMPLAINT: Expresses anger, threats of reporting, or spam grievances
- UNKNOWN: Ambiguous or uninterpretable response

Message:
\"\"\"{reply_text}\"\"\"

Generate:
1. classification: The chosen category
2. sentiment: Positive, Neutral, or Negative
3. summary: Concise 1-sentence synopsis of prospect's stance
4. suggested_reply: Polite, contextual response draft (leave empty if UNSUBSCRIBE or COMPLAINT)
5. requires_human_review: true/false
"""
        schema = """{
  "classification": "INTERESTED",
  "sentiment": "Positive",
  "summary": "string",
  "suggested_reply": "string",
  "requires_human_review": true
}"""
        try:
            res = await ai_router.generate_structured(prompt, schema)
            if res.get("classification") in cls.INTENT_CATEGORIES:
                return res
        except Exception as e:
            logger.warning(f"AI classification failed, using regex fallback: {e}")

        # Deterministic regex heuristic fallback
        lower = reply_text.lower()
        if any(w in lower for w in ["unsubscribe", "stop", "remove me", "don't email", "do not contact", "opt out"]):
            return {"classification": "UNSUBSCRIBE", "sentiment": "Negative", "summary": "Prospect requested opt-out.", "suggested_reply": "", "requires_human_review": False}
        if any(w in lower for w in ["spam", "report you", "harassment", "furious"]):
            return {"classification": "COMPLAINT", "sentiment": "Negative", "summary": "Prospect expressed complaint.", "suggested_reply": "", "requires_human_review": True}
        if any(w in lower for w in ["out of office", "auto-reply", "vacation until", "away from my desk"]):
            return {"classification": "OUT_OF_OFFICE", "sentiment": "Neutral", "summary": "Automated out of office notice.", "suggested_reply": "", "requires_human_review": False}
        if any(w in lower for w in ["call", "meet", "calendar", "schedule", "zoom", "chat this week"]):
            return {"classification": "MEETING_REQUEST", "sentiment": "Positive", "summary": "Prospect requested to schedule a meeting.", "suggested_reply": "I'd be glad to chat. Here is my calendar link to pick a convenient slot.", "requires_human_review": True}
        if any(w in lower for w in ["interested", "pricing", "send details", "curious", "sounds good", "tell me more"]):
            return {"classification": "INTERESTED", "sentiment": "Positive", "summary": "Prospect expressed interest in learning more.", "suggested_reply": "Thanks for the note! I've attached a quick overview and would love to share a 5-min demo.", "requires_human_review": True}
        if any(w in lower for w in ["speak to", "contact my colleague", "copied", "talk with"]):
            return {"classification": "REFERRAL", "sentiment": "Neutral", "summary": "Prospect referred to another team member.", "suggested_reply": "Thank you for the introduction! I will reach out to them directly.", "requires_human_review": True}
        if any(w in lower for w in ["not now", "next quarter", "circle back", "busy right now"]):
            return {"classification": "NOT_NOW", "sentiment": "Neutral", "summary": "Prospect requested follow-up at a later date.", "suggested_reply": "Understood completely. I'll make a note to follow up next quarter.", "requires_human_review": False}
        if any(w in lower for w in ["too expensive", "already use", "no budget", "happy with current"]):
            return {"classification": "OBJECTION", "sentiment": "Neutral", "summary": "Prospect raised an objection.", "suggested_reply": "I understand you're currently covered. Would you be open to a quick comparison benchmark for future reference?", "requires_human_review": True}

        return {"classification": "UNKNOWN", "sentiment": "Neutral", "summary": "General inquiry received.", "suggested_reply": "Thank you for getting back to us. How can we best assist you?", "requires_human_review": True}

    @classmethod
    async def _apply_stop_conditions(
        cls,
        category: str,
        sender: str,
        conversation: Optional[Conversation],
        body_text: str,
        db: Session,
    ) -> List[str]:
        """Enforces automated sequence pauses, suppressions, and CRM alerts."""
        actions_taken = []
        clean_sender = sender.lower().strip()

        # 1. Any reply PAUSES active sequence for this contact
        members = db.query(CampaignMember).filter(
            CampaignMember.recipient_email == clean_sender,
            CampaignMember.status == "ENROLLED",
        ).all()
        for m in members:
            m.status = "PAUSED"
            actions_taken.append(f"Paused campaign sequence for {clean_sender}")
        db.commit()

        # 2. UNSUBSCRIBE, COMPLAINT, or HARD BOUNCE triggers global suppression
        if category in ["UNSUBSCRIBE", "COMPLAINT"]:
            existing_sup = db.query(SuppressionRecord).filter(SuppressionRecord.recipient == clean_sender).first()
            if not existing_sup:
                sup = SuppressionRecord(
                    recipient=clean_sender,
                    channel="ALL",
                    reason=f"REPLY_{category}",
                )
                db.add(sup)
                actions_taken.append(f"Added {clean_sender} to global suppression list ({category})")
            db.commit()

        # 3. INTERESTED or MEETING_REQUEST creates high-priority CRM tasks & activity
        if category in ["INTERESTED", "MEETING_REQUEST"]:
            company_id = conversation.company_id if conversation else None
            contact_id = conversation.contact_id if conversation else None

            task = CRMTask(
                title=f"PROSPECT ACTION: {category.replace('_', ' ').title()} from {clean_sender}",
                description=f"Prospect replied:\n\"{body_text}\"\n\nReview conversation and respond promptly.",
                priority="urgent",
                company_id=company_id,
            )
            db.add(task)

            act = Activity(
                activity_type="STATUS_CHANGE",
                title=f"High Intent Inbound: {category}",
                description=f"Inbound reply classified as {category}.",
                company_id=company_id,
                contact_id=contact_id,
            )
            db.add(act)
            db.commit()
            actions_taken.append(f"Created urgent CRM task ({task.title})")

        return actions_taken

