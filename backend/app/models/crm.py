"""CRM Core Database Models: Companies, Contacts, Deals, Pipelines, Activities, Tasks, Meetings."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, Float, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.guid import GUID


class Company(Base):
    """Business account / company managed in CRM."""

    __tablename__ = "companies"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    domain = Column(String(255), index=True)
    website = Column(String(500))
    industry = Column(String(200), index=True)
    size_range = Column(String(50))  # e.g. "1-10", "11-50", "51-200"
    location = Column(String(255))
    description = Column(Text)
    tech_stack = Column(Text)  # JSON or comma-separated
    annual_revenue = Column(String(100))
    status = Column(String(50), default="active", index=True)
    lead_id = Column(GUID(), nullable=True, index=True)  # Associated BusinessLead if converted

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    contacts = relationship("Contact", back_populates="company", cascade="all, delete-orphan")
    deals = relationship("Deal", back_populates="company", cascade="all, delete-orphan")
    activities = relationship("Activity", back_populates="company", cascade="all, delete-orphan")
    tasks = relationship("CRMTask", back_populates="company", cascade="all, delete-orphan")
    meetings = relationship("Meeting", back_populates="company", cascade="all, delete-orphan")
    call_logs = relationship("CallLog", back_populates="company", cascade="all, delete-orphan")
    notes = relationship("Note", back_populates="company", cascade="all, delete-orphan")
    emails = relationship("Email", back_populates="company", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Company(id={self.id}, name='{self.name}', domain='{self.domain}')>"


class Contact(Base):
    """Individual person / decision maker at a company."""

    __tablename__ = "contacts"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    company_id = Column(GUID(), ForeignKey("companies.id", ondelete="CASCADE"), nullable=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), default="")
    email = Column(String(255), index=True)
    phone = Column(String(100))
    job_title = Column(String(200))
    department = Column(String(100))
    linkedin_url = Column(String(500))
    is_decision_maker = Column(Boolean, default=False)
    reachability_status = Column(String(50), default="unverified")  # verified, unverified, bounced, opted_out
    lead_id = Column(GUID(), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    company = relationship("Company", back_populates="contacts")
    deals = relationship("Deal", back_populates="contact")
    activities = relationship("Activity", back_populates="contact")
    meetings = relationship("Meeting", back_populates="contact")
    call_logs = relationship("CallLog", back_populates="contact")
    notes = relationship("Note", back_populates="contact")
    emails = relationship("Email", back_populates="contact")
    tasks = relationship("CRMTask", back_populates="contact")

    def __repr__(self):
        return f"<Contact(id={self.id}, name='{self.first_name} {self.last_name}', email='{self.email}')>"


class Pipeline(Base):
    """Sales pipeline definition."""

    __tablename__ = "pipelines"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    stages = relationship("PipelineStage", back_populates="pipeline", cascade="all, delete-orphan", order_by="PipelineStage.stage_order")
    deals = relationship("Deal", back_populates="pipeline")


class PipelineStage(Base):
    """Individual stage in a sales pipeline."""

    __tablename__ = "pipeline_stages"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    pipeline_id = Column(GUID(), ForeignKey("pipelines.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    stage_order = Column(Integer, default=0)
    probability = Column(Float, default=0.2)  # 0.0 to 1.0
    is_closed_won = Column(Boolean, default=False, nullable=False)
    is_closed_lost = Column(Boolean, default=False, nullable=False)

    # Relationships
    pipeline = relationship("Pipeline", back_populates="stages")
    deals = relationship("Deal", back_populates="stage")


class Deal(Base):
    """Sales opportunity / deal entity."""

    __tablename__ = "deals"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False, index=True)
    company_id = Column(GUID(), ForeignKey("companies.id", ondelete="CASCADE"), nullable=True, index=True)
    contact_id = Column(GUID(), ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True, index=True)
    pipeline_id = Column(GUID(), ForeignKey("pipelines.id", ondelete="SET NULL"), nullable=True, index=True)
    stage_id = Column(GUID(), ForeignKey("pipeline_stages.id", ondelete="SET NULL"), nullable=True, index=True)
    amount = Column(Float, default=0.0)
    currency = Column(String(10), default="USD")
    status = Column(String(50), default="open", index=True)  # open, won, lost, abandoned
    probability = Column(Float, default=0.2)
    expected_close_date = Column(DateTime, nullable=True)
    lost_reason = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    company = relationship("Company", back_populates="deals")
    contact = relationship("Contact", back_populates="deals")
    pipeline = relationship("Pipeline", back_populates="deals")
    stage = relationship("PipelineStage", back_populates="deals")
    activities = relationship("Activity", back_populates="deal", cascade="all, delete-orphan")
    call_logs = relationship("CallLog", back_populates="deal")
    notes = relationship("Note", back_populates="deal", cascade="all, delete-orphan")
    emails = relationship("Email", back_populates="deal")
    tasks = relationship("CRMTask", back_populates="deal")


class Activity(Base):
    """Timeline activity: notes, calls, emails, status changes, tasks."""

    __tablename__ = "activities"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    activity_type = Column(String(50), nullable=False, index=True)  # NOTE, CALL, EMAIL, MEETING, TASK, STATUS_CHANGE
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    company_id = Column(GUID(), ForeignKey("companies.id", ondelete="CASCADE"), nullable=True, index=True)
    contact_id = Column(GUID(), ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True, index=True)
    deal_id = Column(GUID(), ForeignKey("deals.id", ondelete="CASCADE"), nullable=True, index=True)
    lead_id = Column(GUID(), nullable=True, index=True)
    activity_metadata = Column(Text, nullable=True)  # JSON serialized metadata

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    company = relationship("Company", back_populates="activities")
    contact = relationship("Contact", back_populates="activities")
    deal = relationship("Deal", back_populates="activities")


class CRMTask(Base):
    """CRM Action Item / Follow-up Task."""

    __tablename__ = "crm_tasks"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    due_date = Column(DateTime, nullable=True, index=True)
    priority = Column(String(20), default="medium")  # low, medium, high, urgent
    status = Column(String(50), default="pending", index=True)  # pending, in_progress, completed, cancelled
    company_id = Column(GUID(), ForeignKey("companies.id", ondelete="SET NULL"), nullable=True, index=True)
    contact_id = Column(GUID(), ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True, index=True)
    deal_id = Column(GUID(), ForeignKey("deals.id", ondelete="SET NULL"), nullable=True, index=True)
    assigned_to = Column(String(100), nullable=True)
    related_entity_type = Column(String(50), nullable=True)  # company, contact, deal, lead
    related_entity_id = Column(GUID(), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    company = relationship("Company", back_populates="tasks")
    contact = relationship("Contact", back_populates="tasks")
    deal = relationship("Deal", back_populates="tasks")


class Meeting(Base):
    """Calendar meeting with contact or company."""

    __tablename__ = "meetings"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    company_id = Column(GUID(), ForeignKey("companies.id", ondelete="CASCADE"), nullable=True, index=True)
    contact_id = Column(GUID(), ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True, index=True)
    deal_id = Column(GUID(), ForeignKey("deals.id", ondelete="SET NULL"), nullable=True, index=True)
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=False)
    agenda = Column(Text, nullable=True)
    meeting_url = Column(String(500), nullable=True)
    status = Column(String(50), default="scheduled")  # scheduled, completed, cancelled, no_show
    prep_notes = Column(Text, nullable=True)  # AI briefing notes

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    company = relationship("Company", back_populates="meetings")
    contact = relationship("Contact", back_populates="meetings")


class CallLog(Base):
    """Phone call tracking log."""

    __tablename__ = "call_logs"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    contact_id = Column(GUID(), ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True, index=True)
    company_id = Column(GUID(), ForeignKey("companies.id", ondelete="CASCADE"), nullable=True, index=True)
    deal_id = Column(GUID(), ForeignKey("deals.id", ondelete="SET NULL"), nullable=True, index=True)
    direction = Column(String(20), nullable=False, index=True)  # INBOUND, OUTBOUND
    duration_seconds = Column(Integer, default=0, nullable=False)
    phone_number = Column(String(100), index=True)
    recording_url = Column(String(500), nullable=True)
    transcript = Column(Text, nullable=True)
    outcome = Column(String(50), nullable=True)  # CONNECTED, NO_ANSWER, VOICEMAIL, BUSY
    notes = Column(Text, nullable=True)
    call_started_at = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    created_by = Column(String(100), nullable=True)

    # Relationships
    contact = relationship("Contact", back_populates="call_logs")
    company = relationship("Company", back_populates="call_logs")
    deal = relationship("Deal", back_populates="call_logs")

    def __repr__(self):
        return f"<CallLog(id={self.id}, direction='{self.direction}', phone='{self.phone_number}', outcome='{self.outcome}')>"


class Note(Base):
    """Manual note on lead/company/contact/deal."""

    __tablename__ = "notes"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    content = Column(Text, nullable=False)
    company_id = Column(GUID(), ForeignKey("companies.id", ondelete="CASCADE"), nullable=True, index=True)
    contact_id = Column(GUID(), ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True, index=True)
    deal_id = Column(GUID(), ForeignKey("deals.id", ondelete="CASCADE"), nullable=True, index=True)
    lead_id = Column(GUID(), nullable=True, index=True)
    is_pinned = Column(Boolean, default=False, nullable=False, index=True)
    created_by = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    contact = relationship("Contact", back_populates="notes")
    company = relationship("Company", back_populates="notes")
    deal = relationship("Deal", back_populates="notes")

    def __repr__(self):
        return f"<Note(id={self.id}, content='{self.content[:50]}...', is_pinned={self.is_pinned})>"


class Email(Base):
    """Email interaction tracking."""

    __tablename__ = "emails"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    contact_id = Column(GUID(), ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True, index=True)
    company_id = Column(GUID(), ForeignKey("companies.id", ondelete="CASCADE"), nullable=True, index=True)
    deal_id = Column(GUID(), ForeignKey("deals.id", ondelete="SET NULL"), nullable=True, index=True)
    subject = Column(String(500), nullable=True)
    to_email = Column(String(255), nullable=True, index=True)
    from_email = Column(String(255), nullable=True)
    sent_message_id = Column(String(255), nullable=True, index=True)
    tracking_token = Column(String(100), nullable=True, unique=True, index=True)
    open_count = Column(Integer, default=0)
    body_text = Column(Text, nullable=True)
    body_html = Column(Text, nullable=True)
    direction = Column(String(20), nullable=False, index=True)  # INBOUND, OUTBOUND
    status = Column(String(50), default="draft", nullable=False, index=True)  # draft, sent, delivered, opened, clicked, replied, bounced
    opened_at = Column(DateTime, nullable=True)
    clicked_at = Column(DateTime, nullable=True)
    replied_at = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    contact = relationship("Contact", back_populates="emails")
    company = relationship("Company", back_populates="emails")
    deal = relationship("Deal", back_populates="emails")

    def __repr__(self):
        return f"<Email(id={self.id}, subject='{self.subject}', direction='{self.direction}', status='{self.status}')>"

