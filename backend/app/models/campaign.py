"""Advanced Campaign Management and Multi-Touch Follow-up Sequences."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.guid import GUID


class CampaignMember(Base):
    """Enrollment record of a lead or contact inside a specific campaign."""

    __tablename__ = "campaign_members"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(GUID(), ForeignKey("outreach_campaigns.id", ondelete="CASCADE"), nullable=False, index=True)
    lead_id = Column(GUID(), nullable=True, index=True)
    contact_id = Column(GUID(), nullable=True, index=True)
    recipient_email = Column(String(255), nullable=False, index=True)
    
    # Statuses: ENROLLED, IN_PROGRESS, PAUSED, COMPLETED, UNSUBSCRIBED, BOUNCED
    status = Column(String(50), default="ENROLLED", index=True)
    current_step_number = Column(Integer, default=0)
    next_step_due_at = Column(DateTime, nullable=True, index=True)
    last_step_sent_at = Column(DateTime, nullable=True)
    
    enrolled_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class FollowupSequence(Base):
    """Sequence blueprint defining multi-touch cadences with stop conditions."""

    __tablename__ = "followup_sequences"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Campaign Types:
    # B2B_PROSPECTING, NEWSLETTER, NURTURE, RE_ENGAGEMENT, INBOUND_FOLLOWUP
    campaign_type = Column(String(50), default="B2B_PROSPECTING", index=True)
    is_active = Column(Boolean, default=True, index=True)
    
    stop_on_reply = Column(Boolean, default=True)
    stop_on_meeting = Column(Boolean, default=True)
    stop_on_unsubscribe = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    steps = relationship("FollowupStep", back_populates="sequence", cascade="all, delete-orphan", order_by="FollowupStep.step_number")


class FollowupStep(Base):
    """Individual touchpoint in a sequence with configurable delay and channel."""

    __tablename__ = "followup_steps"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    sequence_id = Column(GUID(), ForeignKey("followup_sequences.id", ondelete="CASCADE"), nullable=False, index=True)
    step_number = Column(Integer, default=1)
    delay_days = Column(Integer, default=0)  # e.g. Day 0, Day 3, Day 7, Day 14
    channel = Column(String(50), default="EMAIL")  # EMAIL, WHATSAPP
    
    subject_template = Column(String(500), nullable=True)
    body_template = Column(Text, nullable=False)
    requires_approval = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    sequence = relationship("FollowupSequence", back_populates="steps")


class CampaignEvent(Base):
    """Audit log of campaign operations (enrollment, pause, resume, completion)."""

    __tablename__ = "campaign_events"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(GUID(), nullable=False, index=True)
    event_type = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
