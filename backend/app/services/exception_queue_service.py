"""Exception Queue Service.

Centralized aggregator for system anomalies requiring human attention:
- Failed workflow executions
- Email delivery bounces and failures
- Legal and compliance review alerts
- High-uncertainty or sensitive inbound replies
- Degraded provider integrations
"""

from typing import Dict, Any, List
import json
import logging
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.workflow import WorkflowExecution
from app.models.deliverability import EmailEvent
from app.models.compliance import DataDeletionRequest
from app.models.outreach import ConversationMessage
from app.models.social import SocialPost
from app.services.provider_health_service import ProviderHealthService

logger = logging.getLogger(__name__)


class ExceptionQueueService:
    """Aggregates all system exceptions into a single triaged queue."""

    @classmethod
    def get_exception_items(cls, db: Session, limit: int = 50) -> Dict[str, Any]:
        """Gathers and ranks all operational exceptions across modules."""
        exceptions = []

        # 1. Failed Workflow Executions
        failed_workflows = db.query(WorkflowExecution).filter(
            WorkflowExecution.status == "FAILED"
        ).order_by(WorkflowExecution.created_at.desc()).limit(15).all()

        for w in failed_workflows:
            exceptions.append({
                "id": f"wf_{w.id}",
                "category": "WORKFLOW_FAILURE",
                "severity": "HIGH",
                "title": f"Workflow Failed: {w.definition.name if w.definition else 'Unknown'}",
                "details": w.error_info or "Unknown workflow execution error",
                "entity_id": str(w.id),
                "timestamp": w.created_at.isoformat() if w.created_at else None,
                "action_type": "RETRY_WORKFLOW",
            })

        # 2. Email Delivery Failures & Bounces
        failed_emails = db.query(EmailEvent).filter(
            EmailEvent.event_type.in_(["BOUNCED", "FAILED", "COMPLAINED"])
        ).order_by(EmailEvent.created_at.desc()).limit(15).all()

        for e in failed_emails:
            exceptions.append({
                "id": f"email_{e.id}",
                "category": "DELIVERABILITY_ALERT",
                "severity": "HIGH" if e.event_type == "COMPLAINED" else "MEDIUM",
                "title": f"Email Event: {e.event_type} ({e.recipient})",
                "details": f"Email to {e.recipient} returned {e.event_type}.",
                "entity_id": str(e.id),
                "timestamp": e.created_at.isoformat(),
                "action_type": "REVIEW_SUPPRESSION",
            })

        # 3. Compliance & Deletion Requests
        pending_deletions = db.query(DataDeletionRequest).filter(
            DataDeletionRequest.status == "REQUESTED"
        ).order_by(DataDeletionRequest.requested_at.desc()).limit(10).all()

        for d in pending_deletions:
            exceptions.append({
                "id": f"gdpr_{d.id}",
                "category": "COMPLIANCE_REQUEST",
                "severity": "URGENT",
                "title": f"GDPR Deletion Request: {d.recipient}",
                "details": f"User requested data erasure (Reason: {d.reason}).",
                "entity_id": str(d.id),
                "timestamp": d.requested_at.isoformat(),
                "action_type": "EXECUTE_DELETION",
            })

        # 4. Sensitive or Unclassified Inbound Replies
        sensitive_replies = db.query(ConversationMessage).filter(
            ConversationMessage.direction == "INBOUND",
            ConversationMessage.ai_classification.in_(["COMPLAINT", "UNKNOWN", "OBJECTION"]),
        ).order_by(ConversationMessage.created_at.desc()).limit(15).all()

        for m in sensitive_replies:
            exceptions.append({
                "id": f"reply_{m.id}",
                "category": "INBOUND_ATTENTION",
                "severity": "MEDIUM",
                "title": f"Inbound Reply ({m.ai_classification}): {m.sender}",
                "details": m.body[:150] + ("..." if len(m.body) > 150 else ""),
                "entity_id": str(m.conversation_id),
                "timestamp": m.created_at.isoformat(),
                "action_type": "REPLY_IN_INBOX",
            })

        # 5. Degraded Integrations
        all_providers = ProviderHealthService.get_all_statuses()
        for p in all_providers:
            p_name = p.get("name") or p.get("provider_name") or "unknown"
            if p.get("status") in ["DEGRADED", "INVALID_CREDENTIALS", "RATE_LIMITED"]:
                exceptions.append({
                    "id": f"prov_{p_name}",
                    "category": "INTEGRATION_ANOMALY",
                    "severity": "HIGH",
                    "title": f"Provider Degraded: {p_name.upper()}",
                    "details": p.get("last_error_message") or f"Provider is {p.get('status')}.",
                    "entity_id": p_name,
                    "timestamp": datetime.utcnow().isoformat(),
                    "action_type": "TEST_INTEGRATION",
                })

        # 6. Social Media Publishing Failures
        failed_social_posts = db.query(SocialPost).filter(
            SocialPost.status == "FAILED"
        ).order_by(SocialPost.updated_at.desc()).limit(10).all()

        for sp in failed_social_posts:
            exceptions.append({
                "id": f"social_{sp.id}",
                "category": "SOCIAL_PUBLISHING_ALERT",
                "severity": "MEDIUM",
                "title": f"Social Publishing Failed: {sp.platform}",
                "details": sp.last_error or "Publishing failed to official platform API.",
                "entity_id": str(sp.id),
                "timestamp": sp.updated_at.isoformat() if sp.updated_at else datetime.utcnow().isoformat(),
                "action_type": "RETRY_SOCIAL_POST",
            })

        return {
            "total_exceptions": len(exceptions),
            "items": exceptions[:limit],
        }
