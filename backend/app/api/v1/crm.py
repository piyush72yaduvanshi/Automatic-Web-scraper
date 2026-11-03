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
