"""Discovery Job database model."""

import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, Text, Integer, Float, DateTime, Index, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class JobStatus(str, Enum):
    """Job status enumeration."""
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class DiscoveryJob(Base):
    """Discovery job tracking."""
    
    __tablename__ = "discovery_jobs"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Search Parameters
    search_query = Column(String(500), nullable=False)
    location = Column(String(500), nullable=False)
    radius_km = Column(Float)
    requested_limit = Column(Integer, default=50)
    
    # Provider Information
    provider = Column(String(100), nullable=False)
    provider_job_id = Column(String(500))
    
    # Job Status
    status = Column(SQLEnum(JobStatus), default=JobStatus.QUEUED, nullable=False, index=True)
    
    # Results
    total_found = Column(Integer, default=0)
    total_enriched = Column(Integer, default=0)
    
    # Error Handling
    error_message = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime)
    
    # Indexes
    __table_args__ = (
        Index("idx_status_created", "status", "created_at"),
        Index("idx_provider_job", "provider", "provider_job_id"),
    )
    
    def __repr__(self):
        return f"<DiscoveryJob(id={self.id}, query='{self.search_query}', status={self.status})>"
