"""CRM API Endpoints: Companies, Contacts, Deals, Kanban Pipelines, Activities, Tasks, Meetings."""

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
import uuid

from app.core.database import get_db
from app.core.security import verify_api_key
from app.services.crm_service import CRMService
from app.models.crm import Company, Contact, Deal, Pipeline, PipelineStage, Activity, CRMTask, Meeting

router = APIRouter(prefix="/crm", tags=["crm"])


# -----------------------------------------------------------------
# Companies
# -----------------------------------------------------------------
@router.get("/companies")
def list_companies(
    search: Optional[str] = None,
    industry: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    companies = CRMService.list_companies(db, search, industry, status, skip, limit)
    return [
        {
            "id": str(c.id),
            "name": c.name,
            "domain": c.domain,
            "website": c.website,
            "industry": c.industry,
            "size_range": c.size_range,
            "location": c.location,
            "status": c.status,
            "deals_count": len(c.deals),
            "contacts_count": len(c.contacts),
            "created_at": c.created_at.isoformat(),
        }
        for c in companies
    ]


@router.post("/companies")
def create_company(
    data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key),
):
    company = CRMService.create_company(db, data)
    return {"id": str(company.id), "name": company.name, "status": "created"}


@router.get("/companies/{company_id}")
def get_company(company_id: str, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == uuid.UUID(company_id)).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return {
        "id": str(company.id),
        "name": company.name,
        "domain": company.domain,
        "website": company.website,
        "industry": company.industry,
        "size_range": company.size_range,
        "location": company.location,
        "description": company.description,
        "tech_stack": company.tech_stack,
        "status": company.status,
        "contacts": [
            {
                "id": str(ct.id),
                "name": f"{ct.first_name} {ct.last_name}".strip(),
                "email": ct.email,
                "phone": ct.phone,
                "job_title": ct.job_title,
                "reachability_status": ct.reachability_status,
            }
            for ct in company.contacts
        ],
        "deals": [
            {
                "id": str(d.id),
                "title": d.title,
                "amount": d.amount,
                "currency": d.currency,
                "status": d.status,
                "stage": d.stage.name if d.stage else None,
            }
            for d in company.deals
        ],
        "created_at": company.created_at.isoformat(),
    }


@router.post("/companies/convert-from-lead/{lead_id}")
def convert_lead_to_company(
    lead_id: str,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key),
):
    try:
        return CRMService.convert_lead_to_company(db, lead_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# -----------------------------------------------------------------
# Contacts
# -----------------------------------------------------------------
@router.get("/contacts")
def list_contacts(
    company_id: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    contacts = CRMService.list_contacts(db, company_id, search, skip, limit)
    return [
        {
            "id": str(c.id),
            "company_id": str(c.company_id) if c.company_id else None,
            "company_name": c.company.name if c.company else None,
            "first_name": c.first_name,
            "last_name": c.last_name,
            "email": c.email,
            "phone": c.phone,
            "job_title": c.job_title,
            "department": c.department,
            "linkedin_url": c.linkedin_url,
            "is_decision_maker": c.is_decision_maker,
            "reachability_status": c.reachability_status,
            "created_at": c.created_at.isoformat(),
        }
        for c in contacts
    ]


@router.post("/contacts")
def create_contact(
    data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key),
):
    contact = CRMService.create_contact(db, data)
    return {"id": str(contact.id), "status": "created"}


# -----------------------------------------------------------------
# Pipelines & Kanban Deals
# -----------------------------------------------------------------
@router.get("/pipelines")
def list_pipelines(db: Session = Depends(get_db)):
    pipeline = CRMService.get_or_create_default_pipeline(db)
    return [
        {
            "id": str(pipeline.id),
            "name": pipeline.name,
            "stages": [
                {
                    "id": str(s.id),
                    "name": s.name,
                    "order": s.stage_order,
                    "probability": s.probability,
                }
                for s in pipeline.stages
            ],
        }
    ]


@router.get("/deals")
def list_deals(
    pipeline_id: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    deals = CRMService.list_deals(db, pipeline_id, status)
    return [
        {
            "id": str(d.id),
            "title": d.title,
            "company_name": d.company.name if d.company else "Unknown",
            "amount": d.amount,
            "currency": d.currency,
            "status": d.status,
            "stage": d.stage.name if d.stage else None,
            "probability": d.probability,
            "created_at": d.created_at.isoformat(),
        }
        for d in deals
    ]


@router.get("/deals/kanban")
def get_kanban(pipeline_id: Optional[str] = None, db: Session = Depends(get_db)):
    return CRMService.get_kanban_board(db, pipeline_id)


@router.post("/deals")
def create_deal(
    data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key),
):
    pipeline = CRMService.get_or_create_default_pipeline(db)
    stage_id = data.get("stage_id") or (str(pipeline.stages[0].id) if pipeline.stages else None)

    deal = Deal(
        title=data["title"],
        company_id=uuid.UUID(str(data["company_id"])) if data.get("company_id") else None,
        contact_id=uuid.UUID(str(data["contact_id"])) if data.get("contact_id") else None,
        pipeline_id=pipeline.id,
        stage_id=uuid.UUID(str(stage_id)) if stage_id else None,
        amount=float(data.get("amount", 0.0)),
        currency=data.get("currency", "USD"),
        status="open",
    )
    db.add(deal)
    db.commit()
    db.refresh(deal)
    return {"id": str(deal.id), "title": deal.title, "status": "created"}


@router.patch("/deals/{deal_id}/stage")
def update_deal_stage(
    deal_id: str,
    stage_id: str = Body(..., embed=True),
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key),
):
    try:
        updated = CRMService.update_deal_stage(db, deal_id, stage_id)
        return {"id": str(updated.id), "stage_id": str(updated.stage_id), "status": updated.status}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# -----------------------------------------------------------------
# Activities & Timeline
# -----------------------------------------------------------------
@router.get("/activities")
def list_activities(
    company_id: Optional[str] = None,
    lead_id: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    acts = CRMService.get_timeline(db, company_id, lead_id, limit)
    return [
        {
            "id": str(a.id),
            "activity_type": a.activity_type,
            "title": a.title,
            "description": a.description,
            "company_name": a.company.name if a.company else None,
            "created_at": a.created_at.isoformat(),
        }
        for a in acts
    ]


@router.post("/activities")
def create_activity(
    data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key),
):
    act = CRMService.log_activity(
        db=db,
        activity_type=data.get("activity_type", "NOTE"),
        title=data["title"],
        description=data.get("description"),
        company_id=uuid.UUID(str(data["company_id"])) if data.get("company_id") else None,
        contact_id=uuid.UUID(str(data["contact_id"])) if data.get("contact_id") else None,
        deal_id=uuid.UUID(str(data["deal_id"])) if data.get("deal_id") else None,
    )
    return {"id": str(act.id), "status": "logged"}


# -----------------------------------------------------------------
# Tasks
# -----------------------------------------------------------------
@router.get("/tasks")
def list_tasks(status: Optional[str] = None, db: Session = Depends(get_db)):
    tasks = CRMService.list_tasks(db, status)
    return [
        {
            "id": str(t.id),
            "title": t.title,
            "description": t.description,
            "due_date": t.due_date.isoformat() if t.due_date else None,
            "priority": t.priority,
            "status": t.status,
            "company_name": t.company.name if t.company else None,
            "created_at": t.created_at.isoformat(),
        }
        for t in tasks
    ]


@router.post("/tasks")
def create_task(
    data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key),
):
    task = CRMService.create_task(db, data)
    return {"id": str(task.id), "title": task.title, "status": "created"}


@router.patch("/tasks/{task_id}/complete")
def complete_task(
    task_id: str,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key),
):
    try:
        task = CRMService.complete_task(db, task_id)
        return {"id": str(task.id), "status": task.status}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# -----------------------------------------------------------------
# Meetings
# -----------------------------------------------------------------
@router.get("/meetings")
def list_meetings(db: Session = Depends(get_db)):
    meetings = CRMService.list_meetings(db)
    return [
        {
            "id": str(m.id),
            "title": m.title,
            "company_name": m.company.name if m.company else None,
            "start_time": m.start_time.isoformat(),
            "end_time": m.end_time.isoformat(),
            "agenda": m.agenda,
            "status": m.status,
            "prep_notes": m.prep_notes,
        }
        for m in meetings
    ]


@router.post("/meetings")
async def schedule_meeting(
    data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key),
):
    meeting = await CRMService.schedule_meeting_with_ai_prep(db, data)
    return {"id": str(meeting.id), "title": meeting.title, "status": "scheduled"}


# -----------------------------------------------------------------
# Call Logs
# -----------------------------------------------------------------
@router.get("/call-logs")
def list_call_logs(
    company_id: Optional[str] = None,
    contact_id: Optional[str] = None,
    deal_id: Optional[str] = None,
    direction: Optional[str] = None,
    outcome: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """List call logs with filters."""
    from app.models.crm import CallLog
    
    query = db.query(CallLog)
    
    if company_id:
        query = query.filter(CallLog.company_id == uuid.UUID(company_id))
    if contact_id:
        query = query.filter(CallLog.contact_id == uuid.UUID(contact_id))
    if deal_id:
        query = query.filter(CallLog.deal_id == uuid.UUID(deal_id))
    if direction:
        query = query.filter(CallLog.direction == direction)
    if outcome:
        query = query.filter(CallLog.outcome == outcome)
    
    call_logs = query.order_by(CallLog.created_at.desc()).offset(skip).limit(limit).all()
    
    return [
        {
            "id": str(c.id),
            "direction": c.direction,
            "phone_number": c.phone_number,
            "duration_seconds": c.duration_seconds,
            "outcome": c.outcome,
            "notes": c.notes,
            "company_name": c.company.name if c.company else None,
            "contact_name": f"{c.contact.first_name} {c.contact.last_name}".strip() if c.contact else None,
            "call_started_at": c.call_started_at.isoformat() if c.call_started_at else None,
            "created_at": c.created_at.isoformat(),
        }
        for c in call_logs
    ]


@router.post("/call-logs")
def create_call_log(
    data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key),
):
    """Create a new call log."""
    from app.models.crm import CallLog
    from datetime import datetime
    
    call_log = CallLog(
        id=uuid.uuid4(),
        contact_id=uuid.UUID(str(data["contact_id"])) if data.get("contact_id") else None,
        company_id=uuid.UUID(str(data["company_id"])) if data.get("company_id") else None,
        deal_id=uuid.UUID(str(data["deal_id"])) if data.get("deal_id") else None,
        direction=data["direction"],
        duration_seconds=data.get("duration_seconds", 0),
        phone_number=data.get("phone_number"),
        outcome=data.get("outcome"),
        notes=data.get("notes"),
        call_started_at=datetime.fromisoformat(data["call_started_at"]) if data.get("call_started_at") else None,
        created_by=data.get("created_by"),
    )
    
    db.add(call_log)
    db.commit()
    db.refresh(call_log)
    
    return {"id": str(call_log.id), "status": "created"}


@router.get("/call-logs/{call_log_id}")
def get_call_log(call_log_id: str, db: Session = Depends(get_db)):
    """Get a single call log by ID."""
    from app.models.crm import CallLog
    
    call_log = db.query(CallLog).filter(CallLog.id == uuid.UUID(call_log_id)).first()
    if not call_log:
        raise HTTPException(status_code=404, detail="Call log not found")
    
    return {
        "id": str(call_log.id),
        "direction": call_log.direction,
        "phone_number": call_log.phone_number,
        "duration_seconds": call_log.duration_seconds,
        "outcome": call_log.outcome,
        "notes": call_log.notes,
        "transcript": call_log.transcript,
        "recording_url": call_log.recording_url,
        "company_id": str(call_log.company_id) if call_log.company_id else None,
        "company_name": call_log.company.name if call_log.company else None,
        "contact_id": str(call_log.contact_id) if call_log.contact_id else None,
        "contact_name": f"{call_log.contact.first_name} {call_log.contact.last_name}".strip() if call_log.contact else None,
        "deal_id": str(call_log.deal_id) if call_log.deal_id else None,
        "call_started_at": call_log.call_started_at.isoformat() if call_log.call_started_at else None,
        "created_at": call_log.created_at.isoformat(),
        "created_by": call_log.created_by,
    }


@router.patch("/call-logs/{call_log_id}")
def update_call_log(
    call_log_id: str,
    data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key),
):
    """Update a call log."""
    from app.models.crm import CallLog
    
    call_log = db.query(CallLog).filter(CallLog.id == uuid.UUID(call_log_id)).first()
    if not call_log:
        raise HTTPException(status_code=404, detail="Call log not found")
    
    if "outcome" in data:
        call_log.outcome = data["outcome"]
    if "notes" in data:
        call_log.notes = data["notes"]
    if "transcript" in data:
        call_log.transcript = data["transcript"]
    if "recording_url" in data:
        call_log.recording_url = data["recording_url"]
    
    db.commit()
    db.refresh(call_log)
    
    return {"id": str(call_log.id), "status": "updated"}


# -----------------------------------------------------------------
# Notes
# -----------------------------------------------------------------
@router.get("/notes")
def list_notes(
    company_id: Optional[str] = None,
    contact_id: Optional[str] = None,
    deal_id: Optional[str] = None,
    lead_id: Optional[str] = None,
    is_pinned: Optional[bool] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """List notes with filters."""
    from app.models.crm import Note
    
    query = db.query(Note)
    
    if company_id:
        query = query.filter(Note.company_id == uuid.UUID(company_id))
    if contact_id:
        query = query.filter(Note.contact_id == uuid.UUID(contact_id))
    if deal_id:
        query = query.filter(Note.deal_id == uuid.UUID(deal_id))
    if lead_id:
        query = query.filter(Note.lead_id == uuid.UUID(lead_id))
    if is_pinned is not None:
        query = query.filter(Note.is_pinned == is_pinned)
    
    # Pinned notes first, then by created_at descending
    notes = query.order_by(Note.is_pinned.desc(), Note.created_at.desc()).offset(skip).limit(limit).all()
    
    return [
        {
            "id": str(n.id),
            "content": n.content,
            "is_pinned": n.is_pinned,
            "company_name": n.company.name if n.company else None,
            "contact_name": f"{n.contact.first_name} {n.contact.last_name}".strip() if n.contact else None,
            "deal_title": n.deal.title if n.deal else None,
            "created_by": n.created_by,
            "created_at": n.created_at.isoformat(),
            "updated_at": n.updated_at.isoformat(),
        }
        for n in notes
    ]


@router.post("/notes")
def create_note(
    data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key),
):
    """Create a new note."""
    from app.models.crm import Note
    
    note = Note(
        id=uuid.uuid4(),
        content=data["content"],
        company_id=uuid.UUID(str(data["company_id"])) if data.get("company_id") else None,
        contact_id=uuid.UUID(str(data["contact_id"])) if data.get("contact_id") else None,
        deal_id=uuid.UUID(str(data["deal_id"])) if data.get("deal_id") else None,
        lead_id=uuid.UUID(str(data["lead_id"])) if data.get("lead_id") else None,
        is_pinned=data.get("is_pinned", False),
        created_by=data.get("created_by"),
    )
    
    db.add(note)
    db.commit()
    db.refresh(note)
    
    return {"id": str(note.id), "status": "created"}


@router.get("/notes/{note_id}")
def get_note(note_id: str, db: Session = Depends(get_db)):
    """Get a single note by ID."""
    from app.models.crm import Note
    
    note = db.query(Note).filter(Note.id == uuid.UUID(note_id)).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    return {
        "id": str(note.id),
        "content": note.content,
        "is_pinned": note.is_pinned,
        "company_id": str(note.company_id) if note.company_id else None,
        "company_name": note.company.name if note.company else None,
        "contact_id": str(note.contact_id) if note.contact_id else None,
        "contact_name": f"{note.contact.first_name} {note.contact.last_name}".strip() if note.contact else None,
        "deal_id": str(note.deal_id) if note.deal_id else None,
        "deal_title": note.deal.title if note.deal else None,
        "lead_id": str(note.lead_id) if note.lead_id else None,
        "created_by": note.created_by,
        "created_at": note.created_at.isoformat(),
        "updated_at": note.updated_at.isoformat(),
    }


@router.patch("/notes/{note_id}")
def update_note(
    note_id: str,
    data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key),
):
    """Update a note."""
    from app.models.crm import Note
    from datetime import datetime
    
    note = db.query(Note).filter(Note.id == uuid.UUID(note_id)).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    if "content" in data:
        note.content = data["content"]
    if "is_pinned" in data:
        note.is_pinned = data["is_pinned"]
    
    note.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(note)
    
    return {"id": str(note.id), "status": "updated"}


@router.delete("/notes/{note_id}")
def delete_note(
    note_id: str,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key),
):
    """Delete a note."""
    from app.models.crm import Note
    
    note = db.query(Note).filter(Note.id == uuid.UUID(note_id)).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    db.delete(note)
    db.commit()
    
    return {"id": str(note_id), "status": "deleted"}


# -----------------------------------------------------------------
# Emails
# -----------------------------------------------------------------
@router.get("/emails")
def list_emails(
    company_id: Optional[str] = None,
    contact_id: Optional[str] = None,
    deal_id: Optional[str] = None,
    direction: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """List emails with filters."""
    from app.models.crm import Email
    
    query = db.query(Email)
    
    if company_id:
        query = query.filter(Email.company_id == uuid.UUID(company_id))
    if contact_id:
        query = query.filter(Email.contact_id == uuid.UUID(contact_id))
    if deal_id:
        query = query.filter(Email.deal_id == uuid.UUID(deal_id))
    if direction:
        query = query.filter(Email.direction == direction)
    if status:
        query = query.filter(Email.status == status)
    
    emails = query.order_by(Email.created_at.desc()).offset(skip).limit(limit).all()
    
    return [
        {
            "id": str(e.id),
            "subject": e.subject,
            "direction": e.direction,
            "status": e.status,
            "company_name": e.company.name if e.company else None,
            "contact_name": f"{e.contact.first_name} {e.contact.last_name}".strip() if e.contact else None,
            "sent_at": e.sent_at.isoformat() if e.sent_at else None,
            "opened_at": e.opened_at.isoformat() if e.opened_at else None,
            "clicked_at": e.clicked_at.isoformat() if e.clicked_at else None,
            "replied_at": e.replied_at.isoformat() if e.replied_at else None,
            "created_at": e.created_at.isoformat(),
        }
        for e in emails
    ]


@router.post("/emails")
def create_email(
    data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key),
):
    """Create a new email record."""
    from app.models.crm import Email
    
    email = Email(
        id=uuid.uuid4(),
        contact_id=uuid.UUID(str(data["contact_id"])) if data.get("contact_id") else None,
        company_id=uuid.UUID(str(data["company_id"])) if data.get("company_id") else None,
        deal_id=uuid.UUID(str(data["deal_id"])) if data.get("deal_id") else None,
        subject=data.get("subject"),
        body_text=data.get("body_text"),
        body_html=data.get("body_html"),
        direction=data["direction"],
        status=data.get("status", "draft"),
    )
    
    db.add(email)
    db.commit()
    db.refresh(email)
    
    return {"id": str(email.id), "status": "created"}


@router.get("/emails/{email_id}")
def get_email(email_id: str, db: Session = Depends(get_db)):
    """Get a single email by ID."""
    from app.models.crm import Email
    
    email = db.query(Email).filter(Email.id == uuid.UUID(email_id)).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    return {
        "id": str(email.id),
        "subject": email.subject,
        "body_text": email.body_text,
        "body_html": email.body_html,
        "direction": email.direction,
        "status": email.status,
        "company_id": str(email.company_id) if email.company_id else None,
        "company_name": email.company.name if email.company else None,
        "contact_id": str(email.contact_id) if email.contact_id else None,
        "contact_name": f"{email.contact.first_name} {email.contact.last_name}".strip() if email.contact else None,
        "deal_id": str(email.deal_id) if email.deal_id else None,
        "sent_at": email.sent_at.isoformat() if email.sent_at else None,
        "opened_at": email.opened_at.isoformat() if email.opened_at else None,
        "clicked_at": email.clicked_at.isoformat() if email.clicked_at else None,
        "replied_at": email.replied_at.isoformat() if email.replied_at else None,
        "created_at": email.created_at.isoformat(),
    }


@router.patch("/emails/{email_id}")
def update_email_tracking(
    email_id: str,
    data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key),
):
    """Update email tracking information."""
    from app.models.crm import Email
    from datetime import datetime
    
    email = db.query(Email).filter(Email.id == uuid.UUID(email_id)).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    if "status" in data:
        email.status = data["status"]
    if "opened_at" in data:
        email.opened_at = datetime.fromisoformat(data["opened_at"]) if data["opened_at"] else None
    if "clicked_at" in data:
        email.clicked_at = datetime.fromisoformat(data["clicked_at"]) if data["clicked_at"] else None
    if "replied_at" in data:
        email.replied_at = datetime.fromisoformat(data["replied_at"]) if data["replied_at"] else None
    if "sent_at" in data:
        email.sent_at = datetime.fromisoformat(data["sent_at"]) if data["sent_at"] else None
    
    db.commit()
    db.refresh(email)
    
    return {"id": str(email.id), "status": "updated"}
