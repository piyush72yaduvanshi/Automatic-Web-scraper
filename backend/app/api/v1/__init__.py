"""API v1 router."""

from fastapi import APIRouter

from app.api.v1 import discovery, leads, health, stats

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(stats.router)
api_router.include_router(discovery.router)
api_router.include_router(leads.router)
