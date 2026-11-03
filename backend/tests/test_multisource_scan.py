"""Tests for multi-source discovery, search radar, AI service, and scan streaming."""

import pytest
from app.providers.discovery.serpapi_provider import SerpApiProvider
from app.providers.discovery.orchestrator import MultiSourceDiscoveryOrchestrator
from app.services.ai_service import AIService
from app.extractors import SocialExtractor, EmailExtractor, PhoneExtractor


def test_serpapi_normalization():
    provider = SerpApiProvider()
    raw_data = {
        "title": "Elite Dental Hospital",
        "type": "Dentist",
        "address": "123 Park Road, Hazratganj, Lucknow, Uttar Pradesh 226001, India",
        "phone": "+91 98765 43210",
        "website": "https://www.elitedental.com",
        "rating": 4.9,
        "reviews": 150,
        "place_id": "test_place_123",
    }

    norm = provider.normalize_business(raw_data, "Lucknow, India")
    assert norm["business_name"] == "Elite Dental Hospital"
    assert norm["category"] == "Dentist"
    assert norm["city"] == "Lucknow"
    assert norm["phone"] == "+91 98765 43210"
    assert norm["source_provider"] == "serpapi"


def test_orchestrator_deduplication():
    orch = MultiSourceDiscoveryOrchestrator()
    items = [
        {"business_name": "Clinic Plus", "website": "https://clinicplus.com", "city": "Lucknow"},
        {"business_name": "clinic plus", "website": "https://clinicplus.com", "city": "Lucknow"},
        {"business_name": "Unique Care", "website": "https://uniquecare.com", "city": "Lucknow"},
    ]
    deduped = orch._deduplicate_businesses(items)
    assert len(deduped) == 2


def test_ai_heuristic_analysis():
    result = AIService._heuristic_analysis(
        name="Realtooth Clinic",
        category="Dentist",
        location="Lucknow",
        site_text="Realtooth was founded by Dr. Anand Agarwal. Contact info@realtooth.in or call +91 8081151128.",
        search_snippets=["Dr. Anand Agarwal BDS MDS", "Realtooth best clinic"],
        raw_contacts={
            "website": "https://realtooth.in",
            "emails": [{"email": "info@realtooth.in"}],
            "phones": [{"original": "+91 8081151128", "normalized": "+918081151128"}],
            "social_profiles": [{"platform": "INSTAGRAM", "url": "https://instagram.com/realtooth"}],
        }
    )

    assert result["quality_score"] >= 70
    assert len(result["verified_emails"]) >= 1
    assert len(result["verified_phones"]) >= 1
    assert "Realtooth" in result["summary"]


def test_social_extractor_all_platforms():
    html = """
    <a href="https://www.linkedin.com/company/apex-corp/">LinkedIn</a>
    <a href="https://www.instagram.com/apex_dental/">Instagram</a>
    <a href="https://www.facebook.com/apexdentalclinic/">Facebook</a>
    <a href="https://x.com/apexdental">X</a>
    """
    socials = SocialExtractor.extract_from_html(html, "https://apex.com")
    platforms = {s["platform"] for s in socials}
    assert "LINKEDIN" in platforms
    assert "INSTAGRAM" in platforms
    assert "FACEBOOK" in platforms
    assert "X" in platforms

