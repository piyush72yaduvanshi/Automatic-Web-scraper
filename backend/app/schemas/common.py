"""Common schemas and utilities."""

from typing import Generic, TypeVar, List, Optional
from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Pagination parameters."""
    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper."""
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    
    model_config = {"from_attributes": True}


class HealthResponse(BaseModel):
    """Health check response."""
    status: Optional[str] = None
    overall: str
    database: Optional[str] = None
    postgres: str
    redis: Optional[str] = None
    minio: Optional[str] = None
    version: str


class StatsResponse(BaseModel):
    """Statistics response."""
    total_leads: int
    total_jobs: int
    emails_found: int
    phones_found: int
    social_profiles_found: int
    jobs_completed: int
    jobs_failed: int
    jobs_running: int
