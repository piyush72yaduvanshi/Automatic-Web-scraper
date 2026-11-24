"""Automation configuration and exception tracking models."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Boolean, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class AutomationSettings(Base):
    """Configuration settings for automation behavior."""
    
    __tablename__ = "automation_settings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    setting_key = Column(String(100), nullable=False, unique=True, index=True)
    setting_value = Column(Text, nullable=False)
    data_type = Column(String(20), default="boolean")  # boolean, integer, string, json
    description = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class LeadException(Base):
    """Exceptions and failures during lead automation processing."""
    
    __tablename__ = "lead_exceptions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    exception_type = Column(String(100), nullable=False, index=True)
    reason = Column(Text, nullable=False)
    severity = Column(String(20), default="warning", index=True)  # info, warning, error, critical
    resolved = Column(Boolean, default=False, index=True)
    resolution_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    resolved_at = Column(DateTime, nullable=True)
    
    __table_args__ = (
        Index("idx_exception_lead_type", "lead_id", "exception_type"),
        Index("idx_exception_severity_resolved", "severity", "resolved"),
    )
