"""Pydantic schemas for API request/response validation."""

from app.schemas.lead import (
    BusinessLeadBase,
    BusinessLeadCreate,
    BusinessLeadResponse,
    LeadContactResponse,
    LeadSocialProfileResponse,
    LeadDetailResponse,
    LeadListResponse,
)
from app.schemas.discovery import (
    DiscoveryJobCreate,
    DiscoveryJobResponse,
    DiscoveryJobDetail,
    DiscoveryJobListResponse,
)
from app.schemas.common import PaginationParams, PaginatedResponse

__all__ = [
    "BusinessLeadBase",
    "BusinessLeadCreate",
    "BusinessLeadResponse",
    "LeadContactResponse",
    "LeadSocialProfileResponse",
    "LeadDetailResponse",
    "LeadListResponse",
    "DiscoveryJobCreate",
    "DiscoveryJobResponse",
    "DiscoveryJobDetail",
    "DiscoveryJobListResponse",
    "PaginationParams",
    "PaginatedResponse",
]
