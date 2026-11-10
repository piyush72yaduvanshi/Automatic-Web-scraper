"""Discovery Schedule Automation Pydantic schemas."""

from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field

from app.models.discovery_schedule import ScheduleType, TargetType, DiscoveryRunStatus


# Discovery Target Schemas
class DiscoveryTargetBase(BaseModel):
    """Base discovery target schema."""
    target_type: TargetType
    target_value: str = Field(..., min_length=1, max_length=255)
    priority: int = Field(default=0, ge=0)


class DiscoveryTargetCreate(DiscoveryTargetBase):
    """Schema for creating a discovery target."""
    pass


class DiscoveryTargetResponse(DiscoveryTargetBase):
    """Discovery target response schema."""
    id: UUID
    schedule_id: UUID
    created_at: datetime
    
    model_config = {"from_attributes": True}


# Discovery Schedule Schemas
class DiscoveryScheduleBase(BaseModel):
    """Base discovery schedule schema."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    is_active: bool = Field(default=True)
    schedule_type: ScheduleType = Field(default=ScheduleType.DAILY)
    cron_expression: Optional[str] = Field(None, max_length=100)
    interval_hours: Optional[int] = Field(None, ge=1, le=168)  # Max 1 week
    max_leads_per_run: int = Field(default=50, ge=1, le=1000)


class DiscoveryScheduleCreate(DiscoveryScheduleBase):
    """Schema for creating a discovery schedule."""
    targets: List[DiscoveryTargetCreate] = Field(default_factory=list)


class DiscoveryScheduleUpdate(BaseModel):
    """Schema for updating a discovery schedule."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    schedule_type: Optional[ScheduleType] = None
    cron_expression: Optional[str] = Field(None, max_length=100)
    interval_hours: Optional[int] = Field(None, ge=1, le=168)
    max_leads_per_run: Optional[int] = Field(None, ge=1, le=1000)


class DiscoveryScheduleResponse(DiscoveryScheduleBase):
    """Discovery schedule response schema."""
    id: UUID
    last_run_at: Optional[datetime]
    next_run_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    targets: List[DiscoveryTargetResponse] = Field(default_factory=list)
    
    model_config = {"from_attributes": True}


# Discovery Run Schemas
class DiscoveryRunResponse(BaseModel):
    """Discovery run response schema."""
    id: UUID
    schedule_id: Optional[UUID]
    status: DiscoveryRunStatus
    leads_discovered: int
    target_snapshot: Optional[Dict[str, Any]]
    error_message: Optional[str]
    started_at: datetime
    completed_at: Optional[datetime]
    
    model_config = {"from_attributes": True}


class DiscoveryScheduleWithRuns(DiscoveryScheduleResponse):
    """Discovery schedule with execution history."""
    recent_runs: List[DiscoveryRunResponse] = Field(default_factory=list)
    
    model_config = {"from_attributes": True}
