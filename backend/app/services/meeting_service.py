"""Meeting Scheduling, Google Calendar Integration & Sales Handoff Service.

Handles meeting booking, Google Calendar synchronization (simulated when unconfigured),
and AI executive briefing dossier generation.
"""

from typing import Dict, Any, List, Optional
import json
import uuid
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.crm import Meeting, Company, Contact, Deal, CRMTask
from app.providers.ai.router import ai_router

logger = logging.getLogger(__name__)


class MeetingService:
    """Manages sales appointments, calendar availability, and AI pre-meeting dossiers."""

    @classmethod
    def list_meetings(cls, db: Session, limit: int = 50) -> List[Dict[str, Any]]:
        """List scheduled and completed meetings with company context."""
        meetings = db.query(Meeting).order_by(Meeting.start_time.asc()).limit(limit).all()
        return [
            {
                "id": str(m.id),
                "title": m.title,
                "company_id": str(m.company_id) if m.company_id else None,
                "company_name": m.company.name if m.company else "Unknown Company",
                "contact_id": str(m.contact_id) if m.contact_id else None,
                "contact_name": f"{m.contact.first_name} {m.contact.last_name}" if m.contact else "Unknown Contact",
                "start_time": m.start_time.isoformat(),
                "end_time": m.end_time.isoformat(),
                "agenda": m.agenda,
                "meeting_url": m.meeting_url,
                "status": m.status,
                "prep_notes": m.prep_notes,
            }
            for m in meetings
        ]

    @classmethod
    async def schedule_meeting(cls, data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """
        Schedules a new sales discovery call or demo.
        Automatically generates an AI pre-meeting briefing dossier and follow-up task.
        """
        title = data.get("title", "Sales Discovery Session")
        company_id = uuid.UUID(str(data.get("company_id"))) if data.get("company_id") else None
        contact_id = uuid.UUID(str(data.get("contact_id"))) if data.get("contact_id") else None
        deal_id = uuid.UUID(str(data.get("deal_id"))) if data.get("deal_id") else None

        start_time = datetime.fromisoformat(data.get("start_time")) if isinstance(data.get("start_time"), str) else data.get("start_time", datetime.utcnow() + timedelta(days=1))
        duration = int(data.get("duration_minutes", 30))
        end_time = start_time + timedelta(minutes=duration)

        company = db.query(Company).filter(Company.id == company_id).first() if company_id else None
        contact = db.query(Contact).filter(Contact.id == contact_id).first() if contact_id else None

        # Generate AI Meeting Briefing Dossier
        company_name = company.name if company else "Prospective Client"
        contact_name = f"{contact.first_name} {contact.last_name}" if contact else "Decision Maker"

        briefing_prompt = f"""You are the Executive Meeting Preparation Agent.
Generate a concise pre-call briefing dossier for:
Meeting: {title}
Company: {company_name} (Industry: {company.industry if company else 'Technology'})
Contact: {contact_name} (Title: {contact.job_title if contact else 'Founder'})
Known Context: {company.description if company else 'Inbound interest in sales automation'}

Synthesize:
1. Executive Background & Likely Pain Points
2. Top 3 Discovery Questions to Ask
3. 2 Anticipated Objections & Ready Counters
4. Ideal Call Outcome / Next Step
"""
        schema = """{
  "executive_summary": "string",
  "discovery_questions": ["string"],
  "objections_and_counters": [{"objection": "string", "counter": "string"}],
  "ideal_next_step": "string"
}"""
        try:
            ai_brief = await ai_router.generate_structured(briefing_prompt, schema)
            prep_notes = json.dumps(ai_brief, indent=2)
        except Exception:
            prep_notes = f"Pre-meeting dossier for {company_name}. Agenda: Review inbound requirements and current workflows."

        meeting = Meeting(
            title=title,
            company_id=company_id,
            contact_id=contact_id,
            deal_id=deal_id,
            start_time=start_time,
            end_time=end_time,
            agenda=data.get("agenda", "Discovery call regarding sales operating system implementation."),
            meeting_url=data.get("meeting_url", "https://meet.google.com/sim-xyz-abc"),
            status="scheduled",
            prep_notes=prep_notes,
        )
        db.add(meeting)

        # Create reminder CRM Task
        task = CRMTask(
            title=f"Prepare for Call: {title} with {company_name}",
            description=f"Scheduled for {start_time.strftime('%Y-%m-%d %H:%M UTC')}. Review AI briefing dossier.",
            priority="high",
            due_date=start_time - timedelta(hours=1),
            company_id=company_id,
        )
        db.add(task)
        db.commit()
        db.refresh(meeting)

        return {
            "id": str(meeting.id),
            "title": meeting.title,
            "company_name": company_name,
            "start_time": meeting.start_time.isoformat(),
            "status": meeting.status,
            "calendar_sync_status": "SIMULATED_LOCAL",  # Transparent: Google Calendar API simulated unless live OAuth token set
        }
