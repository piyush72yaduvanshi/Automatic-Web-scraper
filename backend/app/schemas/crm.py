"""CRM-related Pydantic schemas for CallLog, Note, Email."""

from typing import Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


# ========== Call Log Schemas ==========

class CallLogBase(BaseModel):
    """Base call log schema."""
    contact_id: Optional[UUID] = None
    company_id: Optional[UUID] = None
    deal_id: Optional[UUID] = None
    direction: str = Field(..., pattern="^(INBOUND|OUTBOUND)$")
    duration_seconds: int = Field(default=0, ge=0)
    phone_number: Optional[str] = Field(None, max_length=100)
    outcome: Optional[str] = Field(None, max_length=50)  # CONNECTED, NO_ANSWER, VOICEMAIL, BUSY
    notes: Optional[str] = None
    call_started_at: Optional[datetime] = None


class CallLogCreate(CallLogBase):
    """Schema for creating a call log."""
    pass


class CallLogUpdate(BaseModel):
    """Schema for updating a call log."""
    outcome: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None
    transcript: Optional[str] = None
    recording_url: Optional[str] = Field(None, max_length=500)
    duration_seconds: Optional[int] = Field(None, ge=0)


class CallLogResponse(CallLogBase):
    """Call log response schema."""
    id: UUID
    recording_url: Optional[str] = None
    transcript: Optional[str] = None
    created_at: datetime
    created_by: Optional[str] = None
    
    # Enriched fields
    company_name: Optional[str] = None
    contact_name: Optional[str] = None
    
    model_config = {"from_attributes": True}


# ========== Note Schemas ==========

class NoteBase(BaseModel):
    """Base note schema."""
    content: str = Field(..., min_length=1)
    company_id: Optional[UUID] = None
    contact_id: Optional[UUID] = None
    deal_id: Optional[UUID] = None
    lead_id: Optional[UUID] = None
    is_pinned: bool = False


class NoteCreate(NoteBase):
    """Schema for creating a note."""
    pass


class NoteUpdate(BaseModel):
    """Schema for updating a note."""
    content: Optional[str] = Field(None, min_length=1)
    is_pinned: Optional[bool] = None


class NoteResponse(NoteBase):
    """Note response schema."""
    id: UUID
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    # Enriched fields
    company_name: Optional[str] = None
    contact_name: Optional[str] = None
    deal_title: Optional[str] = None
    
    model_config = {"from_attributes": True}


# ========== Email Schemas ==========

class EmailBase(BaseModel):
    """Base email schema."""
    contact_id: Optional[UUID] = None
    company_id: Optional[UUID] = None
    deal_id: Optional[UUID] = None
    subject: Optional[str] = Field(None, max_length=500)
    body_text: Optional[str] = None
    body_html: Optional[str] = None
    direction: str = Field(..., pattern="^(INBOUND|OUTBOUND)$")


class EmailCreate(EmailBase):
    """Schema for creating an email."""
    pass


class EmailUpdate(BaseModel):
    """Schema for updating email tracking."""
    status: Optional[str] = Field(None, pattern="^(draft|sent|delivered|opened|clicked|replied|bounced)$")
    opened_at: Optional[datetime] = None
    clicked_at: Optional[datetime] = None
    replied_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None


class EmailResponse(EmailBase):
    """Email response schema."""
    id: UUID
    status: str
    opened_at: Optional[datetime] = None
    clicked_at: Optional[datetime] = None
    replied_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    created_at: datetime
    
    # Enriched fields
    company_name: Optional[str] = None
    contact_name: Optional[str] = None
    
    model_config = {"from_attributes": True}


# ========== CRMTask Enhanced Schemas (with new fields) ==========

class CRMTaskBase(BaseModel):
    """Base CRM task schema."""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: str = Field(default="medium", pattern="^(low|medium|high|urgent)$")
    status: str = Field(default="pending", pattern="^(pending|in_progress|completed|cancelled)$")
    company_id: Optional[UUID] = None
    contact_id: Optional[UUID] = None
    deal_id: Optional[UUID] = None
    assigned_to: Optional[str] = Field(None, max_length=100)


class CRMTaskCreate(CRMTaskBase):
    """Schema for creating a CRM task."""
    pass


class CRMTaskUpdate(BaseModel):
    """Schema for updating a CRM task."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: Optional[str] = Field(None, pattern="^(low|medium|high|urgent)$")
    status: Optional[str] = Field(None, pattern="^(pending|in_progress|completed|cancelled)$")
    assigned_to: Optional[str] = None


class CRMTaskResponse(CRMTaskBase):
    """CRM task response schema."""
    id: UUID
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    # Enriched fields
    company_name: Optional[str] = None
    contact_name: Optional[str] = None
    deal_title: Optional[str] = None
    
    model_config = {"from_attributes": True}
