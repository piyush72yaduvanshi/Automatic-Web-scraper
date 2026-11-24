"""Automated Reporting & Optimization Service.

Computes Daily, Weekly, and Monthly operational snapshots based strictly on
real database events, and generates AI optimization recommendations.
"""

from typing import Dict, Any, List, Optional
import json
import uuid
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.reporting import ReportSnapshot
from app.models.business_lead import BusinessLead
from app.models.crm import Deal, Company, Meeting, CRMTask
from app.models.outreach import OutreachApproval, ConversationMessage, SuppressionRecord
from app.models.deliverability import EmailEvent
from app.models.orchestration import AgentRun
from app.providers.ai.router import ai_router

logger = logging.getLogger(__name__)


class ReportingService:
    """Computes daily, weekly, and monthly analytical snapshots from real database state."""

    @classmethod
    def list_reports(cls, db: Session, report_type: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """List historical report snapshots."""
        q = db.query(ReportSnapshot)
        if report_type:
            q = q.filter(ReportSnapshot.report_type == report_type.upper())
        snaps = q.order_by(ReportSnapshot.created_at.desc()).limit(limit).all()
        return [
            {
                "id": str(s.id),
                "report_type": s.report_type,
                "period_start": s.period_start.isoformat(),
                "period_end": s.period_end.isoformat(),
                "executive_summary": s.executive_summary,
                "metrics": json.loads(s.metrics_json) if s.metrics_json else {},
                "recommendations": json.loads(s.recommendations_json) if s.recommendations_json else [],
                "created_at": s.created_at.isoformat(),
            }
            for s in snaps
        ]

    @classmethod
    async def generate_report(cls, report_type: str, db: Session) -> Dict[str, Any]:
        """
        Generates and persists a new operational report snapshot.
        report_type: DAILY, WEEKLY, or MONTHLY.
        """
        r_type = report_type.upper()
        now = datetime.utcnow()

        if r_type == "DAILY":
            start_date = now - timedelta(days=1)
        elif r_type == "WEEKLY":
            start_date = now - timedelta(days=7)
        else:
            r_type = "MONTHLY"
            start_date = now - timedelta(days=30)

        # 1. Compute real metrics from database
        leads_discovered = db.query(BusinessLead).filter(BusinessLead.created_at >= start_date).count()
        leads_qualified = db.query(BusinessLead).filter(
            BusinessLead.created_at >= start_date,
            BusinessLead.qualification_status == "Qualified",
        ).count()

        approvals_prepared = db.query(OutreachApproval).filter(OutreachApproval.created_at >= start_date).count()
        approvals_sent = db.query(OutreachApproval).filter(
            OutreachApproval.created_at >= start_date,
            OutreachApproval.status == "SENT",
        ).count()

        inbound_replies = db.query(ConversationMessage).filter(
            ConversationMessage.created_at >= start_date,
            ConversationMessage.direction == "INBOUND",
        ).count()

        interested_replies = db.query(ConversationMessage).filter(
            ConversationMessage.created_at >= start_date,
            ConversationMessage.ai_classification == "INTERESTED",
        ).count()

        meetings_scheduled = db.query(Meeting).filter(Meeting.created_at >= start_date).count()
        suppression_events = db.query(SuppressionRecord).filter(SuppressionRecord.opted_out_at >= start_date).count()
        bounces = db.query(EmailEvent).filter(EmailEvent.created_at >= start_date, EmailEvent.event_type == "BOUNCED").count()

        deals_won = db.query(Deal).filter(Deal.created_at >= start_date, Deal.status == "won").count()
        won_revenue = sum(d.amount for d in db.query(Deal).filter(Deal.created_at >= start_date, Deal.status == "won").all())

        metrics = {
            "period": f"{start_date.strftime('%Y-%m-%d')} to {now.strftime('%Y-%m-%d')}",
            "leads_discovered": leads_discovered,
            "leads_qualified": leads_qualified,
            "qualification_rate_percent": round((leads_qualified / leads_discovered * 100), 1) if leads_discovered > 0 else 0.0,
            "outreach_prepared": approvals_prepared,
            "outreach_sent": approvals_sent,
            "inbound_replies": inbound_replies,
            "interested_replies": interested_replies,
            "meetings_scheduled": meetings_scheduled,
            "suppression_events": suppression_events,
            "bounces_recorded": bounces,
            "deals_won": deals_won,
            "revenue_won": won_revenue,
        }

        # 2. AI Synthesis for Executive Summary and Strategic Optimization Recommendations
        prompt = f"""You are the Chief Sales & Operations Optimization Agent.
Analyze these real CRM and outreach performance metrics for the {r_type} period:
{json.dumps(metrics, indent=2)}

Provide:
1. 'executive_summary': A direct 2-3 sentence assessment of sales throughput and pipeline conversion.
2. 'recommendations': A list of 3 concrete, data-backed operational improvements (e.g. ICP tightening, sequence cadence, or follow-up urgency).
"""
        schema = """{
  "executive_summary": "string",
  "recommendations": ["string"]
}"""
        try:
            ai_res = await ai_router.generate_structured(prompt, schema)
            summary = ai_res.get("executive_summary", f"{r_type} report summary: {leads_discovered} leads discovered, {leads_qualified} qualified.")
            recommendations = ai_res.get("recommendations", ["Continue monitoring campaign bounce rates", "Follow up with interested leads within 2 hours"])
        except Exception:
            summary = f"{r_type.title()} summary: {leads_discovered} leads processed, {meetings_scheduled} meetings booked, and {deals_won} deals closed."
            recommendations = ["Review qualification criteria for lower scoring accounts", "Maintain daily review of pending outreach approvals"]

        snapshot = ReportSnapshot(
            report_type=r_type,
            period_start=start_date,
            period_end=now,
            metrics_json=json.dumps(metrics),
            executive_summary=summary,
            recommendations_json=json.dumps(recommendations),
        )
        db.add(snapshot)
        db.commit()
        db.refresh(snapshot)

        return {
            "id": str(snapshot.id),
            "report_type": snapshot.report_type,
            "period_start": snapshot.period_start.isoformat(),
            "period_end": snapshot.period_end.isoformat(),
            "summary": summary,
            "metrics": metrics,
            "recommendations": recommendations,
        }

