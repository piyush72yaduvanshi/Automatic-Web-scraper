"""Analytics & Metrics Aggregation Service.

Calculates real business metrics, pipeline conversion rates, discovery yields,
and agent execution telemetry directly from the database.
"""

from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.business_lead import BusinessLead
from app.models.lead_contact import LeadContact, ContactType
from app.models.lead_social_profile import LeadSocialProfile
from app.models.discovery_job import DiscoveryJob
from app.models.crm import Company, Deal, CRMTask, Meeting
from app.models.outreach import OutreachCampaign, OutreachApproval
from app.models.orchestration import AgentRun


class AnalyticsService:
    """Aggregates and computes platform-wide operational and sales intelligence KPIs."""

    @classmethod
    def get_dashboard_overview(cls, db: Session) -> Dict[str, Any]:
        """Real-time analytics computed strictly from stored database entities."""
        # Leads KPIs
        total_leads = db.query(BusinessLead).count()
        qualified_leads = db.query(BusinessLead).filter(
            (BusinessLead.status == "qualified") | (BusinessLead.qualification_status == "Qualified")
        ).count()
        rejected_leads = db.query(BusinessLead).filter(
            (BusinessLead.status == "rejected") | (BusinessLead.qualification_status == "Rejected")
        ).count()

        avg_score_row = db.query(func.avg(BusinessLead.qualification_score)).scalar()
        avg_score = round(float(avg_score_row), 1) if avg_score_row is not None else 50.0

        # Channel availability
        total_emails = db.query(LeadContact).filter(LeadContact.contact_type == ContactType.EMAIL).count()
        total_phones = db.query(LeadContact).filter(LeadContact.contact_type == ContactType.PHONE).count()
        total_socials = db.query(LeadSocialProfile).count()

        # Deals & Pipeline KPIs
        deals = db.query(Deal).all()
        active_deals = [d for d in deals if d.status == "open"]
        won_deals = [d for d in deals if d.status == "won"]
        lost_deals = [d for d in deals if d.status == "lost"]

        pipeline_value = sum(d.amount for d in active_deals)
        won_value = sum(d.amount for d in won_deals)

        # Tasks & Meetings
        pending_tasks = db.query(CRMTask).filter(CRMTask.status == "pending").count()
        scheduled_meetings = db.query(Meeting).filter(Meeting.status == "scheduled").count()

        # Outreach & Approval KPIs
        pending_approvals = db.query(OutreachApproval).filter(OutreachApproval.status == "PENDING").count()
        approved_sent = db.query(OutreachApproval).filter(OutreachApproval.status == "SENT").count()

        campaigns = db.query(OutreachCampaign).all()
        total_sent = sum(c.sent_count for c in campaigns)
        total_replies = sum(c.replied_count for c in campaigns)
        reply_rate = f"{(total_replies / total_sent * 100):.1f}%" if total_sent > 0 else "0.0%"

        # AI Agent Telemetry
        total_runs = db.query(AgentRun).count()
        completed_runs = db.query(AgentRun).filter(AgentRun.status == "COMPLETED").count()
        ai_success_rate = f"{(completed_runs / total_runs * 100):.1f}%" if total_runs > 0 else "100.0%"
        total_cost = db.query(func.sum(AgentRun.estimated_cost_usd)).scalar() or 0.0

        # Leads by category / industry
        categories_query = (
            db.query(BusinessLead.category, func.count(BusinessLead.id))
            .filter(BusinessLead.category != None)
            .group_by(BusinessLead.category)
            .order_by(func.count(BusinessLead.id).desc())
            .limit(6)
            .all()
        )
        leads_by_category = [{"category": cat or "Uncategorized", "count": count} for cat, count in categories_query]

        # Leads by top cities
        cities_query = (
            db.query(BusinessLead.city, func.count(BusinessLead.id))
            .filter(BusinessLead.city != None)
            .group_by(BusinessLead.city)
            .order_by(func.count(BusinessLead.id).desc())
            .limit(6)
            .all()
        )
        leads_by_city = [{"city": city or "Unknown", "count": count} for city, count in cities_query]

        return {
            "leads": {
                "total": total_leads,
                "qualified": qualified_leads,
                "rejected": rejected_leads,
                "average_qualification_score": avg_score,
                "total_emails": total_emails,
                "total_phones": total_phones,
                "total_social_profiles": total_socials,
                "by_category": leads_by_category,
                "by_city": leads_by_city,
            },
            "pipeline": {
                "active_deals_count": len(active_deals),
                "open_pipeline_value": pipeline_value,
                "won_deals_count": len(won_deals),
                "won_value": won_value,
                "lost_deals_count": len(lost_deals),
            },
            "tasks_and_calendar": {
                "pending_tasks": pending_tasks,
                "scheduled_meetings": scheduled_meetings,
                "pending_approvals": pending_approvals,
            },
            "outreach": {
                "approved_sent_count": approved_sent,
                "total_campaign_sent": total_sent,
                "total_campaign_replies": total_replies,
                "reply_rate": reply_rate,
            },
            "ai_telemetry": {
                "total_agent_runs": total_runs,
                "completed_runs": completed_runs,
                "success_rate": ai_success_rate,
                "estimated_cost_usd": round(float(total_cost), 4),
            },
        }
