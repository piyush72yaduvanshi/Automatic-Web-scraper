"""Outreach & Communication Database Models: Campaigns, Steps, Approvals, Conversations, Suppression."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.guid import GUID


class OutreachCampaign(Base):
    """Outreach campaign running multi-step communication sequences."""

    __tablename__ = "outreach_campaigns"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    channel = Column(String(50), default="EMAIL")  # EMAIL, WHATSAPP, MULTI
    status = Column(String(50), default="DRAFT", index=True)  # DRAFT, SCHEDULED, ACTIVE, PAUSED, COMPLETED
    target_audience_filters = Column(Text, nullable=True)  # JSON filters
    total_prospects = Column(Integer, default=0)
    sent_count = Column(Integer, default=0)
    delivered_count = Column(Integer, default=0)
    opened_count = Column(Integer, default=0)
    replied_count = Column(Integer, default=0)
    bounced_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    steps = relationship("CampaignStep", back_populates="campaign", cascade="all, delete-orphan", order_by="CampaignStep.step_number")
    approvals = relationship("OutreachApproval", back_populates="campaign")


class CampaignStep(Base):
    """Individual sequence step inside an outreach campaign."""

    __tablename__ = "campaign_steps"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(GUID(), ForeignKey("outreach_campaigns.id", ondelete="CASCADE"), nullable=False, index=True)
    step_number = Column(Integer, default=1)
    delay_days = Column(Integer, default=0)  # Days after previous step
    template_subject = Column(String(500), nullable=True)
    template_body = Column(Text, nullable=False)
    channel = Column(String(50), default="EMAIL")

    # Relationships
    campaign = relationship("OutreachCampaign", back_populates="steps")


class OutreachApproval(Base):
    """
    CRITICAL HUMAN-IN-THE-LOOP APPROVAL QUEUE.
    Every real outgoing email, WhatsApp, or campaign message MUST be explicitly approved here.
    """

    __tablename__ = "outreach_approvals"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    action_type = Column(String(50), default="SEND_EMAIL")  # SEND_EMAIL, SEND_WHATSAPP
    campaign_id = Column(GUID(), ForeignKey("outreach_campaigns.id", ondelete="SET NULL"), nullable=True, index=True)
    lead_id = Column(GUID(), nullable=True, index=True)
    contact_id = Column(GUID(), nullable=True, index=True)
    recipient_name = Column(String(200), default="Valued Prospect")
    recipient_destination = Column(String(255), nullable=False)  # Email address or E.164 phone
    subject = Column(String(500), nullable=True)
    body_content = Column(Text, nullable=False)
    evidence_context = Column(Text, nullable=True)  # Research reasons & personalization signals
    status = Column(String(50), default="PENDING", index=True)  # PENDING, APPROVED, REJECTED, SENT, FAILED
    approved_at = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    campaign = relationship("OutreachCampaign", back_populates="approvals")


class Conversation(Base):
    """Threaded conversation across channels (Email, WhatsApp)."""

    __tablename__ = "conversations"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    channel = Column(String(50), default="EMAIL", index=True)  # EMAIL, WHATSAPP
    external_thread_id = Column(String(255), nullable=True, index=True)
    subject = Column(String(500), nullable=True)
    contact_id = Column(GUID(), nullable=True, index=True)
    company_id = Column(GUID(), nullable=True, index=True)
    status = Column(String(50), default="ACTIVE", index=True)  # ACTIVE, CLOSED, ARCHIVED
    last_message_at = Column(DateTime, default=datetime.utcnow, index=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    messages = relationship("ConversationMessage", back_populates="conversation", cascade="all, delete-orphan", order_by="ConversationMessage.created_at")


class ConversationMessage(Base):
    """Single message within a threaded conversation."""

    __tablename__ = "conversation_messages"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(GUID(), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    direction = Column(String(20), default="OUTBOUND", index=True)  # INBOUND, OUTBOUND
    sender = Column(String(255), nullable=False)
    recipient = Column(String(255), nullable=False)
    subject = Column(String(500), nullable=True)
    body = Column(Text, nullable=False)
    message_type = Column(String(50), default="text")
    delivery_status = Column(String(50), default="sent")  # queued, sent, delivered, read, bounced, failed
    ai_classification = Column(String(100), nullable=True)  # INTERESTED, OBJECTION, NOT_NOW, UNSUBSCRIBE, QUESTION
    suggested_reply = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")


class SuppressionRecord(Base):
    """Global opt-out and bounce suppression registry."""

    __tablename__ = "suppression_records"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    recipient = Column(String(255), nullable=False, unique=True, index=True)  # Lowercase email or normalized phone
    channel = Column(String(50), default="ALL")  # EMAIL, WHATSAPP, ALL
    reason = Column(String(100), default="UNSUBSCRIBE")  # UNSUBSCRIBE, BOUNCE, COMPLAINT, MANUAL
    opted_out_at = Column(DateTime, default=datetime.utcnow, nullable=False)
