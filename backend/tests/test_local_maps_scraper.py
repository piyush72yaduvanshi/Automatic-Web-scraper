"""Unit tests for Local Google Maps Scraper Provider & Orchestrator integration."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from app.providers.discovery.local_maps_provider import LocalMapsScraperProvider
from app.providers.discovery.orchestrator import MultiSourceDiscoveryOrchestrator


def test_local_maps_scraper_is_configured():
    provider = LocalMapsScraperProvider(base_url="http://localhost:8080")
    # Live engine daemon is running on port 8080
    assert provider.is_configured() is True

    provider_empty = LocalMapsScraperProvider(base_url="http://127.0.0.1:9999")
    assert provider_empty.is_configured() is False


def test_local_maps_scraper_normalization():
    provider = LocalMapsScraperProvider()
    raw_item = {
        "title": "Dr. Smile Dental Care",
        "category": "Dental Clinic",
        "phone": "+91 99887 76655",
        "website": "https://www.drsmilecare.in",
        "address": "12 Gomti Nagar, Lucknow",
        "complete_address": "12 Gomti Nagar, Lucknow, Uttar Pradesh 226010, India",
        "review_rating": 4.8,
        "review_count": 128,
        "latitude": 26.8500,
        "longitude": 80.9500,
        "place_id": "ChIJ_test12345",
        "cid": "987654321012345",
        "emails": ["contact@drsmilecare.in", "info@drsmilecare.in"],
        "instagram": "https://instagram.com/drsmilecare",
        "facebook": "https://facebook.com/drsmilecare",
        "linkedin": "https://linkedin.com/company/drsmilecare",
        "x": "https://x.com/drsmilecare",
    }

    normalized = provider.normalize_business(raw_item, default_location="Lucknow, India")

    assert normalized["business_name"] == "Dr. Smile Dental Care"
    assert normalized["category"] == "Dental Clinic"
    assert normalized["phone"] == "+91 99887 76655"
    assert normalized["website"] == "https://www.drsmilecare.in"
    assert normalized["city"] == "Lucknow"
    assert "4.8" in normalized["description"]
    assert normalized["source_provider"] == "local_maps_scraper"
    assert normalized["provider_external_id"] == "ChIJ_test12345"

    # Verify extracted direct emails & socials
    emails = normalized["emails"]
    assert len(emails) == 2
    assert emails[0]["email"] == "contact@drsmilecare.in"

    socials = {s["platform"]: s["profile_url"] for s in normalized["social_profiles"]}
    assert socials["INSTAGRAM"] == "https://instagram.com/drsmilecare"
    assert socials["FACEBOOK"] == "https://facebook.com/drsmilecare"
    assert socials["LINKEDIN"] == "https://linkedin.com/company/drsmilecare"
    assert socials["X"] == "https://x.com/drsmilecare"


def test_orchestrator_resolves_local_maps_provider():
    orch = MultiSourceDiscoveryOrchestrator()
    provider = orch.get_provider("local_maps")
    assert isinstance(provider, LocalMapsScraperProvider)

    provider_alias = orch.get_provider("local_maps_scraper")
    assert isinstance(provider_alias, LocalMapsScraperProvider)

    provider_kit = orch.get_provider("google_maps_kit")
    assert isinstance(provider_kit, LocalMapsScraperProvider)


@pytest.mark.asyncio
async def test_discover_businesses_mock_flow():
    provider = LocalMapsScraperProvider(base_url="http://localhost:8080")

    mock_download = [
        {
            "title": "Lucknow Dental Excellence",
            "category": "Dentist",
            "phone": "+91 522 123456",
            "website": "https://lucknowdental.com",
            "address": "Hazratganj, Lucknow",
            "complete_address": "Hazratganj, Lucknow, UP, India",
            "emails": ["care@lucknowdental.com"],
            "instagram": "https://instagram.com/lucknowdental",
        }
    ]

    mock_client = AsyncMock()
    mock_geocode_res = MagicMock(status_code=200)
    mock_geocode_res.json.return_value = [{"lat": 26.8467, "lon": 80.9462}]

    mock_create_res = MagicMock(status_code=200)
    mock_create_res.json.return_value = {"id": "test-job-999"}

    mock_poll_res = MagicMock(status_code=200)
    mock_poll_res.json.return_value = {"Status": "ok", "Progress": {"places": 1}}

    mock_dl_res = MagicMock(status_code=200)
    mock_dl_res.json.return_value = mock_download

    async def fake_get(url, *args, **kwargs):
        if "/api/v1/cities" in url:
            return mock_geocode_res
        elif "/download" in url:
            return mock_dl_res
        elif "/api/v1/jobs/" in url:
            return mock_poll_res
        return MagicMock(status_code=404)

    async def fake_post(url, *args, **kwargs):
        if "/api/v1/jobs" in url:
            return mock_create_res
        return MagicMock(status_code=404)

    mock_client.get = AsyncMock(side_effect=fake_get)
    mock_client.post = AsyncMock(side_effect=fake_post)

    with patch("httpx.AsyncClient") as MockAsyncClient:
        MockAsyncClient.return_value.__aenter__.return_value = mock_client

        result = await provider.discover_businesses(
            query="dentist",
            location="Lucknow",
            limit=5
        )

        businesses = result["businesses"]
        assert len(businesses) == 1
        assert businesses[0]["business_name"] == "Lucknow Dental Excellence"
        assert businesses[0]["emails"][0]["email"] == "care@lucknowdental.com"
        assert businesses[0]["social_profiles"][0]["platform"] == "INSTAGRAM"
