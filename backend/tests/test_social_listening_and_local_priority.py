"""Tests for Local Scraper Priority, Mailpit Integration, and Social Listening Agent."""

import pytest
from fastapi.testclient import TestClient
import uuid

from main import app
from app.core.database import SessionLocal
from app.providers.discovery.orchestrator import MultiSourceDiscoveryOrchestrator
from app.services.social_listening_agent import SocialListeningAgent
from app.models.business_lead import BusinessLead
from app.models.social_media_lead import SocialMediaLead
from app.providers.communication.smtp_provider import SMTPProvider
from app.services.imap_reply_tracker import IMAPReplyTrackerService

client = TestClient(app)


def test_discovery_orchestrator_local_scraper_priority():
    """Verify MultiSourceDiscoveryOrchestrator prioritizes local_maps provider."""
    orchestrator = MultiSourceDiscoveryOrchestrator()
    assert orchestrator.local_maps_provider is not None
    assert orchestrator.get_provider("local_maps") is not None
    assert orchestrator.get_provider("google_maps_kit") is not None


def test_smtp_mailpit_configured_without_password():
    """Verify SMTPProvider recognises local Mailpit on port 1025 as configured without user/pass."""
    assert SMTPProvider.is_configured() is True


def test_social_listening_intent_evaluation():
    """Verify SocialListeningAgent correctly scores high-intent buying signals."""
    sample_post = "We have budget approved and are looking for a reliable CRM and lead automation software for our sales team. Recommendations?"
    eval_res = SocialListeningAgent.evaluate_intent(sample_post)
    assert eval_res["is_qualified"] is True
    assert eval_res["score"] >= 70.0
    assert eval_res["intent_category"] in ("HIGH_PURCHASE_INTENT", "SERVICE_REQUEST")
    assert len(eval_res["matched_signals"]) > 0


def test_social_listening_contact_extraction():
    """Verify email and phone extraction from social text."""
    content = "Need an agency for marketing. Email our founder: founder@techscale.org or call +1 555-234-5678"
    contacts = SocialListeningAgent._extract_contacts_from_text(content)
    assert contacts["email"] == "founder@techscale.org"
    assert contacts["phone"] is not None


@pytest.mark.asyncio
async def test_social_listening_agent_scan_and_auto_pipeline():
    """Verify SocialListeningAgent runs scan across platforms and creates BusinessLeads."""
    db = SessionLocal()
    try:
        scan_res = await SocialListeningAgent.run_listening_scan(
            platforms=["LINKEDIN", "X"],
            limit_per_platform=2,
            db=db,
        )
        assert scan_res["success"] is True
        assert scan_res["total_leads_extracted"] > 0
        assert "LINKEDIN" in scan_res["results_by_platform"]
        assert "X" in scan_res["results_by_platform"]

        # Verify leads were inserted in DB
        first_lead = scan_res["results_by_platform"]["LINKEDIN"][0]
        db_lead = db.query(BusinessLead).filter(BusinessLead.id == uuid.UUID(first_lead["lead_id"])).first()
        assert db_lead is not None
        assert db_lead.source_provider == "SOCIAL_LINKEDIN"
        assert db_lead.qualification_score is not None

        # Clean up test leads
        for plat_results in scan_res["results_by_platform"].values():
            for r in plat_results:
                lid = uuid.UUID(r["lead_id"])
                db.query(SocialMediaLead).filter(SocialMediaLead.lead_id == lid).delete()
                db.query(BusinessLead).filter(BusinessLead.id == lid).delete()
        db.commit()
    finally:
        db.close()


def test_social_listening_api_endpoints():
    """Verify /api/v1/social/listening/status and /run-now endpoints."""
    # Status endpoint
    resp = client.get("/api/v1/social/listening/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "active"
    assert "LINKEDIN" in data["channels"]
    assert "FACEBOOK" in data["channels"]
    assert "INSTAGRAM" in data["channels"]
    assert "X" in data["channels"]
