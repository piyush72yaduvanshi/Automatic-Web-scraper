"""Unit and API tests for Webhook subscription, dispatch, and external CRM ingestion."""

import pytest
from unittest.mock import patch, MagicMock
from app.services.webhook_service import WebhookService
from app.models.webhook import WebhookSubscription, WebhookDelivery
from app.models.business_lead import BusinessLead


def test_hmac_signature_generation_and_verification():
    secret = "test_webhook_secret_key_12345"
    payload = b'{"event":"lead.discovered","data":{"name":"Dr Smile"}}'

    signature = WebhookService.generate_signature(payload, secret)
    assert signature.startswith("sha256=")

    # Verify signature
    assert WebhookService.verify_signature(payload, signature, secret) is True
    # Verify without prefix
    assert WebhookService.verify_signature(payload, signature.replace("sha256=", ""), secret) is True
    # Invalid secret or payload
    assert WebhookService.verify_signature(payload, signature, "wrong_secret") is False
    assert WebhookService.verify_signature(b'tampered_payload', signature, secret) is False


def test_webhook_subscription_lifecycle(db):
    sub = WebhookService.create_subscription(
        db=db,
        name="PHP Production CRM",
        target_url="https://crm.example.com/api/v1/leads-webhook",
        events=["lead.discovered", "lead.qualified"],
    )

    assert sub.id is not None
    assert sub.name == "PHP Production CRM"
    assert sub.target_url == "https://crm.example.com/api/v1/leads-webhook"
    assert "lead.discovered" in sub.events
    assert len(sub.secret_key) >= 32

    # List
    subs = WebhookService.list_subscriptions(db=db)
    assert len(subs) >= 1
    assert any(s.id == sub.id for s in subs)

    # Delete
    deleted = WebhookService.delete_subscription(db=db, subscription_id=str(sub.id))
    assert deleted is True

    subs_after = WebhookService.list_subscriptions(db=db)
    assert not any(s.id == sub.id for s in subs_after)


def test_ingest_external_lead_from_php_crm(db):
    lead_payload = {
        "business_name": "Sharma Dental Hospital",
        "category": "Dentist",
        "email": "dr.sharma@sharmadental.com",
        "phone": "+91 98765 00112",
        "website": "https://sharmadental.com",
        "city": "Lucknow",
        "state": "Uttar Pradesh",
        "source_provider": "php_custom_crm",
    }

    result = WebhookService.ingest_external_lead(db=db, payload=lead_payload)

    assert result["success"] is True
    assert result["is_new"] is True
    assert result["lead"]["business_name"] == "Sharma Dental Hospital"
    assert result["lead"]["city"] == "Lucknow"

    # Verify in DB
    lead_db = db.query(BusinessLead).filter(BusinessLead.website == "https://sharmadental.com").first()
    assert lead_db is not None
    assert lead_db.email == "dr.sharma@sharmadental.com"


def test_webhook_api_endpoints(client):
    # 1. Create subscription via REST API
    res = client.post("/api/v1/webhooks/subscriptions", json={
        "name": "External Zapier Hook",
        "target_url": "https://hooks.zapier.com/hooks/catch/123/abc/",
        "events": ["lead.*"],
    })
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    sub_id = data["subscription"]["id"]
    secret_key = data["subscription"]["secret_key"]

    # 2. List subscriptions
    res_list = client.get("/api/v1/webhooks/subscriptions")
    assert res_list.status_code == 200
    items = res_list.json()
    assert any(i["id"] == sub_id for i in items)

    # 3. Verify helper endpoint
    verify_res = client.post("/api/v1/webhooks/verify", json={
        "payload": '{"test":"value"}',
        "signature": WebhookService.generate_signature(b'{"test":"value"}', secret_key),
        "secret_key": secret_key,
    })
    assert verify_res.status_code == 200
    assert verify_res.json()["valid"] is True

    # 4. Ingest lead endpoint
    ingest_res = client.post("/api/v1/webhooks/ingest", json={
        "business_name": "Verma Eye Clinic",
        "email": "info@vermaeye.in",
        "phone": "+91 522 998877",
        "city": "Lucknow",
    })
    assert ingest_res.status_code == 200
    assert ingest_res.json()["success"] is True
    assert ingest_res.json()["lead"]["business_name"] == "Verma Eye Clinic"

    # 5. Clean up
    del_res = client.delete(f"/api/v1/webhooks/subscriptions/{sub_id}")
    assert del_res.status_code == 200
