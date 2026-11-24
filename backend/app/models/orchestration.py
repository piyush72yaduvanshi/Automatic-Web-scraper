"""AI Orchestration, Knowledge Base, Persistent Memory, and Audit Logging Models."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from app.core.database import Base
from app.models.guid import GUID


class AgentRun(Base):
    """Execution telemetry and audit record for specialized AI agents."""

    __tablename__ = "agent_runs"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    agent_name = Column(String(100), nullable=False, index=True)
    task_type = Column(String(100), nullable=False)
    status = Column(String(50), default="PENDING", index=True)  # PENDING, RUNNING, COMPLETED, FAILED, REQUIRES_APPROVAL
    input_parameters = Column(Text, nullable=True)  # JSON input
    output_data = Column(Text, nullable=True)  # JSON output
    error_message = Column(Text, nullable=True)
    execution_steps = Column(Text, nullable=True)  # JSON intermediate steps
    tokens_used = Column(Integer, default=0)
    estimated_cost_usd = Column(Float, default=0.0)
    duration_ms = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True)


class KnowledgeDocument(Base):
    """Knowledge base article, sales playbook, company offering, or case study."""

    __tablename__ = "knowledge_documents"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False, index=True)
    category = Column(String(100), default="SERVICE_OFFERING", index=True)
    # COMPANY_PROFILE, SERVICE_OFFERING, ICP, CASE_STUDY, EMAIL_TEMPLATE, OBJECTION_HANDLING, PLAYBOOK
    content = Column(Text, nullable=False)
    file_type = Column(String(50), default="text")
    file_url = Column(String(500), nullable=True)  # MinIO object storage URL for attachments/assets
    metadata_json = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    chunks = relationship("KnowledgeChunk", back_populates="document", cascade="all, delete-orphan")


class KnowledgeChunk(Base):
    """Text chunk with embedding vector for pgvector RAG semantic search."""

    __tablename__ = "knowledge_chunks"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    document_id = Column(GUID(), ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, default=0)
    chunk_text = Column(Text, nullable=False)
    embedding_vector = Column(Vector(768), nullable=True)  # Native pgvector 768-dim column
    embedding_json = Column(Text, nullable=True)  # Serialized float vector [x1, x2, ...] fallback
    token_count = Column(Integer, default=0)

    # Relationships
    document = relationship("KnowledgeDocument", back_populates="chunks")


class MemoryRecord(Base):
    """Persistent organizational and prospect memory."""

    __tablename__ = "memory_records"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    entity_type = Column(String(50), nullable=False, index=True)  # COMPANY, LEAD, USER_PREFERENCE, QUALIFICATION_RULE
    entity_id = Column(String(255), nullable=True, index=True)
    key = Column(String(100), nullable=False, index=True)
    value = Column(Text, nullable=False)  # JSON payload or string
    confidence = Column(Float, default=1.0)
    source = Column(String(100), default="user")

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class AuditLog(Base):
    """Security and compliance audit trail."""

    __tablename__ = "audit_logs"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    action = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(String(255), nullable=True)
    details = Column(Text, nullable=True)
    ip_address = Column(String(100), nullable=True)

    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

