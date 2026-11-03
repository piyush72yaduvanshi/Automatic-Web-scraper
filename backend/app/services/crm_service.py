"""Full CRM Domain Service: Companies, Contacts, Deals, Pipelines, Activities, Tasks, Meetings."""

import uuid
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.models.crm import (
    Company,
    Contact,
    Pipeline,
    PipelineStage,
    Deal,
    Activity,
    CRMTask,
    Meeting,
)
from app.models.business_lead import BusinessLead
from app.providers.ai.router import ai_router


class CRMService:
    """Core CRM Business Logic and Relationship Engine."""

    # -------------------------------------------------------------
    # Pipeline & Stages
    # -------------------------------------------------------------
    @classmethod
    def get_or_create_default_pipeline(cls, db: Session) -> Pipeline:
        """Ensure a default sales pipeline exists with standard sales stages."""
        pipeline = db.query(Pipeline).filter(Pipeline.is_default == True).first()
        if not pipeline:
            pipeline = Pipeline(name="Default Sales Pipeline", is_default=True)
            db.add(pipeline)
            db.flush()

            default_stages = [
                ("Lead", 0, 0.1),
                ("Qualified", 1, 0.25),
                ("Contacted", 2, 0.4),
                ("Meeting Scheduled", 3, 0.6),
                ("Proposal", 4, 0.75),
                ("Negotiation", 5, 0.9),
                ("Won", 6, 1.0),
                ("Lost", 7, 0.0),
            ]
            for name, order, prob in default_stages:
                stage = PipelineStage(
                    pipeline_id=pipeline.id,
                    name=name,
                    stage_order=order,
                    probability=prob,
                )
                db.add(stage)
            db.commit()
            db.refresh(pipeline)
        return pipeline

    # -------------------------------------------------------------
    # Companies
    # -------------------------------------------------------------
    @classmethod
    def list_companies(
        cls,
        db: Session,
        search: Optional[str] = None,
        industry: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Company]:
        query = db.query(Company)
        if search:
            query = query.filter(Company.name.ilike(f"%{search}%") | Company.domain.ilike(f"%{search}%"))
        if industry:
            query = query.filter(Company.industry.ilike(f"%{industry}%"))
        if status:
            query = query.filter(Company.status == status)
        return query.order_by(desc(Company.created_at)).offset(skip).limit(limit).all()

    @classmethod
    def create_company(cls, db: Session, data: Dict[str, Any]) -> Company:
        company = Company(
            name=data["name"],
            domain=data.get("domain"),
            website=data.get("website"),
            industry=data.get("industry"),
            size_range=data.get("size_range"),
            location=data.get("location"),
            description=data.get("description"),
            tech_stack=data.get("tech_stack"),
            annual_revenue=data.get("annual_revenue"),
            status=data.get("status", "active"),
            lead_id=uuid.UUID(str(data["lead_id"])) if data.get("lead_id") else None,
        )
        db.add(company)
        db.commit()
        db.refresh(company)

        # Log creation activity
        cls.log_activity(
            db=db,
            activity_type="SYSTEM",
            title=f"Company '{company.name}' created in CRM",
            company_id=company.id,
        )
        return company

    @classmethod
    def convert_lead_to_company(cls, db: Session, lead_id: str) -> Dict[str, Any]:
        """Convert a BusinessLead directly into a CRM Company and Contact."""
        lead = db.query(BusinessLead).filter(BusinessLead.id == lead_id).first()
        if not lead:
            raise ValueError(f"Lead not found: {lead_id}")

        # Check if already converted
        existing = db.query(Company).filter(Company.lead_id == lead.id).first()
        if existing:
            return {"company": existing, "message": "Lead was already converted."}

        domain = None
        if lead.website:
            from urllib.parse import urlparse
            parsed = urlparse(lead.website)
            domain = parsed.hostname or lead.website

        company = Company(
            name=lead.business_name,
            domain=domain,
            website=lead.website,
            industry=lead.category,
            location=f"{lead.city or ''}, {lead.state or ''}, {lead.country or ''}".strip(", "),
            description=lead.description or lead.qualification_reasoning,
            lead_id=lead.id,
            status="active",
        )
        db.add(company)
        db.flush()

        # Update lead association
        lead.company_id = company.id
        lead.status = "converted"

        # Transfer contacts
        created_contacts = []
        for c in lead.contacts:
            if c.contact_type.value == "EMAIL":
                contact = Contact(
                    company_id=company.id,
                    first_name=lead.business_name,
                    last_name="Team",
                    email=c.normalized_value or c.original_value,
                    reachability_status="verified" if c.verification_status == "verified" else "unverified",
                    lead_id=lead.id,
                )
                db.add(contact)
                created_contacts.append(contact)
            elif c.contact_type.value == "PHONE" and not created_contacts:
                contact = Contact(
                    company_id=company.id,
                    first_name=lead.business_name,
                    last_name="Office",
                    phone=c.normalized_value or c.original_value,
                    lead_id=lead.id,
                )
                db.add(contact)
                created_contacts.append(contact)

        # Create deal in default pipeline
        pipeline = cls.get_or_create_default_pipeline(db)
        first_stage = pipeline.stages[0] if pipeline.stages else None

        deal = Deal(
            title=f"Opportunity: {company.name}",
            company_id=company.id,
            pipeline_id=pipeline.id,
            stage_id=first_stage.id if first_stage else None,
            amount=5000.0,
            status="open",
        )
        db.add(deal)

        # Log Activity
        cls.log_activity(
            db=db,
            activity_type="STATUS_CHANGE",
            title=f"Converted Lead '{lead.business_name}' to CRM Company & Deal",
            company_id=company.id,
            deal_id=deal.id,
            lead_id=lead.id,
        )

        db.commit()
        db.refresh(company)

        return {
            "company_id": str(company.id),
            "company_name": company.name,
            "deal_id": str(deal.id),
            "contacts_count": len(created_contacts),
        }

    # -------------------------------------------------------------
    # Contacts
    # -------------------------------------------------------------
    @classmethod
    def list_contacts(
        cls,
        db: Session,
        company_id: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Contact]:
        query = db.query(Contact)
        if company_id:
            query = query.filter(Contact.company_id == uuid.UUID(str(company_id)))
        if search:
            query = query.filter(
                Contact.first_name.ilike(f"%{search}%") |
                Contact.last_name.ilike(f"%{search}%") |
                Contact.email.ilike(f"%{search}%")
            )
        return query.order_by(desc(Contact.created_at)).offset(skip).limit(limit).all()

    @classmethod
    def create_contact(cls, db: Session, data: Dict[str, Any]) -> Contact:
        contact = Contact(
            company_id=uuid.UUID(str(data["company_id"])) if data.get("company_id") else None,
            first_name=data["first_name"],
            last_name=data.get("last_name", ""),
            email=data.get("email"),
            phone=data.get("phone"),
            job_title=data.get("job_title"),
            department=data.get("department"),
            linkedin_url=data.get("linkedin_url"),
            is_decision_maker=data.get("is_decision_maker", False),
            reachability_status=data.get("reachability_status", "unverified"),
        )
        db.add(contact)
        db.commit()
        db.refresh(contact)
        return contact

    # -------------------------------------------------------------
    # Deals & Kanban Pipeline
    # -------------------------------------------------------------
    @classmethod
    def list_deals(
        cls,
        db: Session,
        pipeline_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Deal]:
        query = db.query(Deal)
        if pipeline_id:
            query = query.filter(Deal.pipeline_id == uuid.UUID(str(pipeline_id)))
        if status:
            query = query.filter(Deal.status == status)
        return query.order_by(desc(Deal.created_at)).all()

    @classmethod
    def get_kanban_board(cls, db: Session, pipeline_id: Optional[str] = None) -> Dict[str, Any]:
        """Return deals grouped by pipeline stages for Kanban board view."""
        if pipeline_id:
            pipeline = db.query(Pipeline).filter(Pipeline.id == uuid.UUID(str(pipeline_id))).first()
        else:
            pipeline = cls.get_or_create_default_pipeline(db)

        if not pipeline:
            pipeline = cls.get_or_create_default_pipeline(db)

        stages_data = []
        for stage in pipeline.stages:
            stage_deals = db.query(Deal).filter(Deal.stage_id == stage.id, Deal.status == "open").all()
            total_value = sum(d.amount for d in stage_deals)
            stages_data.append({
                "id": str(stage.id),
                "name": stage.name,
                "order": stage.stage_order,
                "probability": stage.probability,
                "total_value": total_value,
                "deals_count": len(stage_deals),
                "deals": [
                    {
                        "id": str(d.id),
                        "title": d.title,
                        "amount": d.amount,
                        "currency": d.currency,
                        "company_name": d.company.name if d.company else "Unknown",
                        "contact_name": f"{d.contact.first_name} {d.contact.last_name}".strip() if d.contact else None,
                        "probability": d.probability,
                        "created_at": d.created_at.isoformat(),
                    }
                    for d in stage_deals
                ]
            })

        return {
            "pipeline_id": str(pipeline.id),
            "pipeline_name": pipeline.name,
            "stages": stages_data,
        }

    @classmethod
    def update_deal_stage(cls, db: Session, deal_id: str, new_stage_id: str) -> Deal:
        deal = db.query(Deal).filter(Deal.id == uuid.UUID(str(deal_id))).first()
        if not deal:
            raise ValueError(f"Deal not found: {deal_id}")

        new_stage = db.query(PipelineStage).filter(PipelineStage.id == uuid.UUID(str(new_stage_id))).first()
        if not new_stage:
            raise ValueError(f"Stage not found: {new_stage_id}")

        old_stage_name = deal.stage.name if deal.stage else "None"
        deal.stage_id = new_stage.id
        deal.probability = new_stage.probability

        # If moved to Won or Lost stage
        if new_stage.name.lower() == "won":
            deal.status = "won"
        elif new_stage.name.lower() == "lost":
            deal.status = "lost"

        # Log activity
        cls.log_activity(
            db=db,
            activity_type="STATUS_CHANGE",
            title=f"Deal '{deal.title}' moved from '{old_stage_name}' to '{new_stage.name}'",
            company_id=deal.company_id,
            deal_id=deal.id,
        )

        db.commit()
        db.refresh(deal)
        return deal

    # -------------------------------------------------------------
    # Activities & Timeline
    # -------------------------------------------------------------
    @classmethod
    def log_activity(
        cls,
        db: Session,
        activity_type: str,
        title: str,
        description: Optional[str] = None,
        company_id: Optional[uuid.UUID] = None,
        contact_id: Optional[uuid.UUID] = None,
        deal_id: Optional[uuid.UUID] = None,
        lead_id: Optional[uuid.UUID] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Activity:
        activity = Activity(
            activity_type=activity_type,
            title=title,
            description=description,
            company_id=company_id,
            contact_id=contact_id,
            deal_id=deal_id,
            lead_id=lead_id,
            activity_metadata=json.dumps(metadata or {}),
        )
        db.add(activity)
        db.commit()
        db.refresh(activity)
        return activity

    @classmethod
    def get_timeline(
        cls,
        db: Session,
        company_id: Optional[str] = None,
        lead_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[Activity]:
        query = db.query(Activity)
        if company_id:
            query = query.filter(Activity.company_id == uuid.UUID(str(company_id)))
        if lead_id:
            query = query.filter(Activity.lead_id == uuid.UUID(str(lead_id)))
        return query.order_by(desc(Activity.created_at)).limit(limit).all()

    # -------------------------------------------------------------
    # Tasks & Follow-ups
    # -------------------------------------------------------------
    @classmethod
    def list_tasks(cls, db: Session, status: Optional[str] = None) -> List[CRMTask]:
        query = db.query(CRMTask)
        if status:
            query = query.filter(CRMTask.status == status)
        return query.order_by(CRMTask.due_date.asc().nullslast()).all()

    @classmethod
    def create_task(cls, db: Session, data: Dict[str, Any]) -> CRMTask:
        due = datetime.fromisoformat(data["due_date"]) if data.get("due_date") else None
        task = CRMTask(
            title=data["title"],
            description=data.get("description"),
            due_date=due,
            priority=data.get("priority", "medium"),
            company_id=uuid.UUID(str(data["company_id"])) if data.get("company_id") else None,
            related_entity_type=data.get("related_entity_type"),
            related_entity_id=uuid.UUID(str(data["related_entity_id"])) if data.get("related_entity_id") else None,
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    @classmethod
    def complete_task(cls, db: Session, task_id: str) -> CRMTask:
        task = db.query(CRMTask).filter(CRMTask.id == uuid.UUID(str(task_id))).first()
        if not task:
            raise ValueError(f"Task not found: {task_id}")
        task.status = "completed"
        task.completed_at = datetime.utcnow()
        db.commit()
        db.refresh(task)
        return task

    # -------------------------------------------------------------
    # Meetings
    # -------------------------------------------------------------
    @classmethod
    def list_meetings(cls, db: Session) -> List[Meeting]:
        return db.query(Meeting).order_by(Meeting.start_time.asc()).all()

    @classmethod
    async def schedule_meeting_with_ai_prep(cls, db: Session, data: Dict[str, Any]) -> Meeting:
        """Schedule meeting and generate AI prep dossier."""
        company_id = uuid.UUID(str(data["company_id"])) if data.get("company_id") else None
        company = db.query(Company).filter(Company.id == company_id).first() if company_id else None

        prep_prompt = f"Prepare a meeting preparation brief for meeting '{data['title']}' with company '{company.name if company else 'Client'}'. Outline key discussion points, potential objections, and discovery questions."
        prep_brief = await ai_router.generate_text(prep_prompt)

        meeting = Meeting(
            title=data["title"],
            company_id=company_id,
            contact_id=uuid.UUID(str(data["contact_id"])) if data.get("contact_id") else None,
            deal_id=uuid.UUID(str(data["deal_id"])) if data.get("deal_id") else None,
            start_time=datetime.fromisoformat(data["start_time"]),
            end_time=datetime.fromisoformat(data["end_time"]),
            agenda=data.get("agenda"),
            meeting_url=data.get("meeting_url"),
            prep_notes=prep_brief,
        )
        db.add(meeting)
        db.commit()
        db.refresh(meeting)
        return meeting
