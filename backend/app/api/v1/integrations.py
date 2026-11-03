"""API endpoints for Integration Configuration and Health Management."""

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from app.core.database import get_db
from app.core.security import verify_api_key
from app.services.provider_health_service import ProviderHealthService

router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.get("", response_model=List[Dict[str, Any]])
def list_integrations(db: Session = Depends(get_db)):
    """List all integrations with their current configuration and health statuses."""
    return ProviderHealthService.get_all_statuses(db)


@router.get("/health", response_model=Dict[str, Any])
def integrations_summary(db: Session = Depends(get_db)):
    """Summary overview of integration health across the platform."""
    statuses = ProviderHealthService.get_all_statuses(db)
    total = len(statuses)
    healthy = sum(1 for s in statuses if s["status"] == "HEALTHY")
    not_configured = sum(1 for s in statuses if s["status"] == "NOT_CONFIGURED")
    degraded = sum(1 for s in statuses if s["status"] in ["DEGRADED", "TEMPORARILY_UNAVAILABLE", "RATE_LIMITED", "INVALID_CREDENTIALS"])
    disabled = sum(1 for s in statuses if s["status"] == "DISABLED")

    overall = "HEALTHY" if degraded == 0 else "DEGRADED"

    return {
        "overall_status": overall,
        "total_integrations": total,
        "healthy_count": healthy,
        "not_configured_count": not_configured,
        "degraded_count": degraded,
        "disabled_count": disabled,
        "integrations": statuses,
    }


@router.post("/{provider_name}/validate")
async def validate_integration(provider_name: str, _: bool = Depends(verify_api_key)):
    """Test and validate connection/credentials for a specific external integration."""
    result = await ProviderHealthService.validate_provider(provider_name)
    return result


@router.patch("/{provider_name}/toggle")
def toggle_integration(
    provider_name: str,
    enabled: bool = Body(..., embed=True),
    _: bool = Depends(verify_api_key),
):
    """Enable or disable a specific integration."""
    success = ProviderHealthService.toggle_provider(provider_name, enabled)
    if not success:
        raise HTTPException(status_code=404, detail=f"Integration '{provider_name}' not found.")
    return {"provider": provider_name, "is_enabled": enabled, "status": "updated"}
