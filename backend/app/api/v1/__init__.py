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
