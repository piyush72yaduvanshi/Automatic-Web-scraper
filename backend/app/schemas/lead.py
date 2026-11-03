"""Lead-related Pydantic schemas."""

from typing import List, Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, HttpUrl

from app.models.lead_contact import ContactType
from app.models.lead_social_profile import SocialPlatform


class BusinessLeadBase(BaseModel):
    """Base business lead schema."""
    business_name: str = Field(..., min_length=1, max_length=500)
    category: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=200)
    state: Optional[str] = Field(None, max_length=200)
    country: Optional[str] = Field(None, max_length=100)
    website: Optional[str] = Field(None, max_length=500)


class BusinessLeadCreate(BusinessLeadBase):
    """Schema for creating a business lead."""
    source_provider: str = Field(..., max_length=100)
    provider_external_id: Optional[str] = Field(None, max_length=500)


class LeadContactResponse(BaseModel):
    """Lead contact response schema."""
    id: UUID
    contact_type: ContactType
    original_value: str
    normalized_value: Optional[str]
    verification_status: str
    source_url: Optional[str]
    collected_at: datetime
    
    model_config = {"from_attributes": True}


class LeadSocialProfileResponse(BaseModel):
    """Lead social profile response schema."""
    id: UUID
    platform: SocialPlatform
    profile_url: str
    verification_status: str
    source_url: Optional[str]
    collected_at: datetime
    
    model_config = {"from_attributes": True}


class BusinessLeadResponse(BusinessLeadBase):
    """Business lead response schema."""
    id: UUID
    source_provider: str
    status: str
    created_at: datetime
    updated_at: datetime
    
    # Counts for related data
    email_count: Optional[int] = 0
    phone_count: Optional[int] = 0
    social_count: Optional[int] = 0
    
    model_config = {"from_attributes": True}


class LeadSourceEvidenceResponse(BaseModel):
    """Lead source evidence schema."""
    id: UUID
    field_name: str
    extracted_value: str
    source_url: str
    provider: Optional[str] = None
    collected_at: datetime
    
    model_config = {"from_attributes": True}


class LeadDetailResponse(BusinessLeadResponse):
    """Detailed lead response with contacts and social profiles."""
    contacts: List[LeadContactResponse] = []
    social_profiles: List[LeadSocialProfileResponse] = []
    source_evidence: List[LeadSourceEvidenceResponse] = []
    
    model_config = {"from_attributes": True}


class LeadListResponse(BaseModel):
    """Paginated list of leads."""
    items: List[BusinessLeadResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
