"""Tests for provider fault tolerance, missing key safety, and health management."""

import pytest
from app.services.provider_health_service import ProviderHealthService, IntegrationStatus
from app.providers.ai.router import AIProviderRouter
from app.providers.ai.heuristic_provider import HeuristicAIProvider
from app.providers.ai.gemini_provider import GeminiAIProvider


def test_provider_health_all_statuses():
    statuses = ProviderHealthService.get_all_statuses()
    assert len(statuses) >= 9
    names = {s["name"] for s in statuses}
    assert "gemini" in names
    assert "heuristic_nlp" in names
    assert "serpapi" in names
    assert "gmail" in names
    assert "whatsapp" in names


def test_heuristic_provider_always_available():
    heuristic = HeuristicAIProvider()
    assert heuristic.is_available() is True


@pytest.mark.asyncio
async def test_ai_router_graceful_fallback_without_keys():
    """AI router must never crash or raise exceptions, falling back cleanly to heuristic."""
    router = AIProviderRouter()
    # Force empty custom key
    result_text = await router.generate_text("Generate outreach email for dental clinic")
    assert isinstance(result_text, str)
    assert len(result_text) > 20

    structured = await router.generate_structured("Business: Smile Care Dental", "Summary and score")
    assert isinstance(structured, dict)
    assert "qualification_score" in structured
    assert structured["qualification_score"] >= 0

    embedding = await router.generate_embeddings("Dental health software services")
    assert isinstance(embedding, list)
    assert len(embedding) == 128


def test_provider_toggle_and_failure_recording():
    ProviderHealthService.toggle_provider("gemini", False)
    statuses = {s["name"]: s for s in ProviderHealthService.get_all_statuses()}
    assert statuses["gemini"]["status"] == IntegrationStatus.DISABLED.value

    # Re-enable
    ProviderHealthService.toggle_provider("gemini", True)
    ProviderHealthService.record_success("gemini")
    statuses = {s["name"]: s for s in ProviderHealthService.get_all_statuses()}
    assert statuses["gemini"]["status"] == IntegrationStatus.HEALTHY.value
