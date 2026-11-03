"""Discovery job schemas."""

from typing import List, Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field

from app.models.discovery_job import JobStatus


class DiscoveryJobCreate(BaseModel):
    """Schema for creating a discovery job."""
    query: str = Field(..., min_length=1, max_length=500, description="Business category or keyword")
    location: str = Field(..., min_length=1, max_length=500, description="City, state, country")
    radius_km: Optional[float] = Field(None, ge=0, le=100, description="Search radius in kilometers")
    limit: int = Field(default=50, ge=1, le=500, description="Maximum number of results")
    
    # Source options
    sources: List[str] = Field(default=["maps"], description="Discovery sources: maps, website")
    
    # Enrichment options
    enrich_emails: bool = Field(default=True, description="Extract email addresses")
    enrich_phones: bool = Field(default=True, description="Extract phone numbers")
    enrich_socials: bool = Field(default=True, description="Extract social profiles")
    
    # Provider preference (optional)
    preferred_provider: Optional[str] = Field(None, description="Preferred provider: apify, outscraper, google_places")


class DiscoveryJobResponse(BaseModel):
    """Discovery job response schema."""
    id: UUID
    search_query: str
    location: str
    radius_km: Optional[float]
    requested_limit: int
    provider: str
    status: JobStatus
    total_found: int
    total_enriched: int
    created_at: datetime
    completed_at: Optional[datetime]
    
    model_config = {"from_attributes": True}


class DiscoveryJobDetail(DiscoveryJobResponse):
    """Detailed discovery job with error information."""
    provider_job_id: Optional[str]
    error_message: Optional[str]
    
    model_config = {"from_attributes": True}


class DiscoveryJobListResponse(BaseModel):
    """Paginated list of discovery jobs."""
    items: List[DiscoveryJobResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
