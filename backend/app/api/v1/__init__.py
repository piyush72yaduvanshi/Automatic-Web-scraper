"""API v1 router."""

from fastapi import APIRouter

from app.api.v1 import (
    health,
    stats,
    discovery,
    leads,
    integrations,
    crm,
    agents,
    outreach,
    knowledge,
    analytics,
    # Phase 2 Routers
    workflows,
    deliverability,
    campaigns,
    sequences,
    compliance,
    content,
    seo,
    meetings,
    reports,
    exceptions,
    social,
    storage,
)

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(stats.router)
api_router.include_router(discovery.router)
api_router.include_router(leads.router)
api_router.include_router(integrations.router)
api_router.include_router(crm.router)
api_router.include_router(agents.router)
api_router.include_router(outreach.router)
api_router.include_router(knowledge.router)
api_router.include_router(analytics.router)

# Phase 2 Routes
api_router.include_router(workflows.router)
api_router.include_router(deliverability.router)
api_router.include_router(campaigns.router)
api_router.include_router(sequences.router)
api_router.include_router(compliance.router)
api_router.include_router(content.router)
api_router.include_router(seo.router)
api_router.include_router(meetings.router)
api_router.include_router(reports.router)
api_router.include_router(exceptions.router)
api_router.include_router(social.router)
api_router.include_router(storage.router)
