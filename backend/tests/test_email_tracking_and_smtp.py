"""Tests for SMTP Provider, IMAP Reply Tracker, and Email/Image Open Tracking."""

import pytest
from fastapi.testclient import TestClient
import uuid

from main import app
from app.providers.communication.smtp_provider import SMTPProvider
from app.services.imap_reply_tracker import IMAPReplyTrackerService
from app.core.database import SessionLocal
from app.models.crm import Email, Activity

client = TestClient(app)


def test_smtp_provider_tracking_injection():
    """Verify SMTPProvider correctly injects 1x1 tracking pixel and personalized image."""
    html = "<html><body><p>Hello Prospect</p></body></html>"
    token = "test_token_abc123"
    personalized_url = "http://localhost:8000/api/v1/email-tracking/image/banner.png"

    injected = SMTPProvider.inject_tracking_elements(
        html_content=html,
        tracking_token=token,
        personalized_image_url=personalized_url,
    )

    assert f"/api/v1/email-tracking/open/{token}.png" in injected
    assert personalized_url in injected
    assert "<img" in injected


def test_smtp_send_simulation_mode():
    """Verify SMTPProvider falls back cleanly to simulation mode when unconfigured."""
    res = SMTPProvider.send_email(
        to_email="prospect@example.com",
        subject="Test Cold Outreach",
        body_html="<p>Test</p>",
    )
    assert res["success"] is True
    assert res["mode"] == "dev_simulation"
    assert "tracking_token" in res
    assert "message_id" in res


def test_email_tracking_open_pixel():
    """Verify GET /api/v1/email-tracking/open/{token}.png returns 1x1 transparent PNG and logs open."""
    db = SessionLocal()
    token = uuid.uuid4().hex
    email_obj = Email(
        id=uuid.uuid4(),
        subject="Pixel Open Test",
        to_email="prospect@test.com",
        tracking_token=token,
        status="sent",
        direction="OUTBOUND",
    )
    db.add(email_obj)
    db.commit()

    resp = client.get(f"/api/v1/email-tracking/open/{token}.png")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/png"
    assert "no-cache" in resp.headers["cache-control"]
    assert len(resp.content) > 0

    # Verify DB was updated
    db.refresh(email_obj)
    assert email_obj.opened_at is not None
    assert email_obj.open_count == 1
    assert email_obj.status == "opened"

    # Subsequent open should increment count
    resp2 = client.get(f"/api/v1/email-tracking/open/{token}.png")
    assert resp2.status_code == 200
    db.refresh(email_obj)
    assert email_obj.open_count == 2

    db.delete(email_obj)
    db.commit()
    db.close()


def test_email_tracking_image_endpoint():
    """Verify GET /api/v1/email-tracking/image/{asset_id} serves dynamic graphic and logs open."""
    db = SessionLocal()
    token = uuid.uuid4().hex
    email_obj = Email(
        id=uuid.uuid4(),
        subject="Image Open Test",
        to_email="banner@test.com",
        tracking_token=token,
        status="sent",
        direction="OUTBOUND",
    )
    db.add(email_obj)
    db.commit()

    resp = client.get(f"/api/v1/email-tracking/image/custom-banner.svg?token={token}")
    assert resp.status_code == 200
    assert "image/svg+xml" in resp.headers["content-type"]
    assert b"<svg" in resp.content

    db.refresh(email_obj)
    assert email_obj.opened_at is not None
    assert email_obj.open_count == 1

    db.delete(email_obj)
    db.commit()
    db.close()


def test_send_smtp_api_endpoint():
    """Verify POST /api/v1/email-tracking/send-smtp registers record and returns tracking URLs."""
    payload = {
        "to_email": "ceo@growthstartup.io",
        "subject": "Scale Your Lead Acquisition Pipeline",
        "body_html": "<p>Hi Founders,</p><p>Check our AI OS.</p>",
        "personalized_image_url": "http://localhost:8000/api/v1/email-tracking/image/badge.svg",
    }
    resp = client.post("/api/v1/email-tracking/send-smtp", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "tracking_token" in data
    assert "tracking_pixel_url" in data
    assert "sent_message_id" in data


def test_poll_imap_api_endpoint():
    """Verify POST /api/v1/email-tracking/poll-replies handles simulation mode safely."""
    resp = client.post("/api/v1/email-tracking/poll-replies?limit=10")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "checked_messages" in data
    assert "matched_replies" in data


def test_email_tracking_stats_endpoint():
    """Verify GET /api/v1/email-tracking/stats returns aggregated metrics."""
    resp = client.get("/api/v1/email-tracking/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_sent" in data
    assert "total_opened" in data
    assert "open_rate_percent" in data
    assert "reply_rate_percent" in data
