"""Native Python Workflow Engine Models (Zero n8n).

Persists workflow definitions, execution states, triggers, steps, and event queues in PostgreSQL/SQLite.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.guid import GUID


class WorkflowDefinition(Base):
    """Declarative workflow definition with trigger, schema, and step graph."""

    __tablename__ = "workflow_definitions"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    version = Column(Integer, default=1)
    
    # Trigger Types:
    # MANUAL, SCHEDULED, NEW_LEAD, LEAD_ENRICHED, LEAD_QUALIFIED, 
    # CAMPAIGN_APPROVED, INCOMING_MESSAGE, REPLY_CLASSIFIED, FOLLOWUP_DUE, 
    # UNSUBSCRIBE, HEALTH_CHANGED
    trigger_type = Column(String(50), default="MANUAL", index=True)
    trigger_config = Column(Text, nullable=True)  # JSON configuration for trigger (cron expression, filter, etc.)
    
    input_schema = Column(Text, nullable=True)  # JSON schema describing expected inputs
    steps_json = Column(Text, nullable=False)  # JSON array of steps and transitions
    retry_config = Column(Text, nullable=True)  # JSON: {"max_retries": 3, "backoff_seconds": 5}
    timeout_seconds = Column(Integer, default=300)
    is_active = Column(Boolean, default=True, index=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    executions = relationship("WorkflowExecution", back_populates="definition", cascade="all, delete-orphan")


class WorkflowExecution(Base):
    """Execution state machine and history of a workflow instance."""

    __tablename__ = "workflow_executions"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(GUID(), ForeignKey("workflow_definitions.id", ondelete="CASCADE"), nullable=False, index=True)
    trigger_event = Column(String(50), default="MANUAL")
    
    # Statuses:
    # PENDING, RUNNING, COMPLETED, FAILED, RETRYING, CANCELLED, WAITING_FOR_APPROVAL
    status = Column(String(50), default="PENDING", index=True)
    current_step_id = Column(String(100), nullable=True)
    
    input_payload = Column(Text, nullable=True)  # JSON input
    step_results = Column(Text, nullable=True)  # JSON dictionary of step outputs
    error_info = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    
    start_time = Column(DateTime, nullable=True)
    completion_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    definition = relationship("WorkflowDefinition", back_populates="executions")


class WorkflowEvent(Base):
    """Event log for event-driven workflow bus."""

    __tablename__ = "workflow_events"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    event_type = Column(String(100), nullable=False, index=True)
    payload = Column(Text, nullable=False)  # JSON payload
    processed = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

