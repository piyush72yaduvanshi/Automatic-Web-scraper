"""Discovery Schedule Automation Models.

Enables scheduled lead discovery with configurable targets and execution tracking.
"""

import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, ForeignKey, Index, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.guid import GUID


class ScheduleType(str, Enum):
    """Schedule type enumeration."""
    HOURLY = "HOURLY"
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    CUSTOM = "CUSTOM"


class TargetType(str, Enum):
    """Discovery target type enumeration."""
    CITY = "CITY"
    STATE = "STATE"
    COUNTRY = "COUNTRY"
    INDUSTRY = "INDUSTRY"
    CATEGORY = "CATEGORY"


class DiscoveryRunStatus(str, Enum):
    """Discovery run status enumeration."""
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class DiscoverySchedule(Base):
    """Scheduled discovery automation configuration."""

    __tablename__ = "discovery_schedules"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    
    # Schedule Configuration
    schedule_type = Column(SQLEnum(ScheduleType), default=ScheduleType.DAILY, nullable=False)
    cron_expression = Column(String(100), nullable=True)  # For CUSTOM schedules
    interval_hours = Column(Integer, nullable=True)  # For HOURLY schedules
    
    # Discovery Limits
    max_leads_per_run = Column(Integer, default=50, nullable=False)
    
    # Execution Tracking
    last_run_at = Column(DateTime, nullable=True, index=True)
    next_run_at = Column(DateTime, nullable=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    targets = relationship(
        "DiscoveryTarget",
        back_populates="schedule",
        cascade="all, delete-orphan"
    )
    runs = relationship(
        "DiscoveryRun",
        back_populates="schedule",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_discovery_schedule_active", "is_active"),
        Index("idx_discovery_schedule_next_run", "next_run_at"),
    )

    def __repr__(self):
        return f"<DiscoverySchedule(id={self.id}, name='{self.name}', active={self.is_active})>"


class DiscoveryTarget(Base):
    """Discovery target configuration (city, state, country, industry, category)."""

    __tablename__ = "discovery_targets"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    schedule_id = Column(GUID(), ForeignKey("discovery_schedules.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Target Configuration
    target_type = Column(SQLEnum(TargetType), nullable=False)
    target_value = Column(String(255), nullable=False)  # e.g., "New York", "Technology", "Restaurant"
    priority = Column(Integer, default=0, nullable=False)  # Higher priority = processed first
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    schedule = relationship("DiscoverySchedule", back_populates="targets")

    __table_args__ = (
        Index("idx_discovery_target_schedule", "schedule_id"),
        Index("idx_discovery_target_type", "target_type"),
    )

    def __repr__(self):
        return f"<DiscoveryTarget(id={self.id}, type={self.target_type}, value='{self.target_value}')>"


class DiscoveryRun(Base):
    """Discovery run execution history and results."""

    __tablename__ = "discovery_runs"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    schedule_id = Column(GUID(), ForeignKey("discovery_schedules.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Execution Status
    status = Column(SQLEnum(DiscoveryRunStatus), default=DiscoveryRunStatus.RUNNING, nullable=False, index=True)
    leads_discovered = Column(Integer, default=0, nullable=False)
    
    # Configuration Snapshot
    target_snapshot = Column(JSON, nullable=True)  # JSON snapshot of targets at execution time
    
    # Error Handling
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    schedule = relationship("DiscoverySchedule", back_populates="runs")

    __table_args__ = (
        Index("idx_discovery_run_status", "status"),
        Index("idx_discovery_run_started", "started_at"),
        Index("idx_discovery_run_schedule", "schedule_id"),
    )

    def __repr__(self):
        return f"<DiscoveryRun(id={self.id}, status={self.status}, leads={self.leads_discovered})>"
