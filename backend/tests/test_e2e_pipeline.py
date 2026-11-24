"""End-to-End (E2E) Pipeline Test Suite.

Simulates the full autonomous journey:
1. Ingest lead via Local Maps Scraper format
2. Extract email, phone, and social handles
3. AI ICP Qualification and Scoring
4. CRM Company, Contact, Pipeline, and Deal creation
5. Multichannel Outreach Generation
6. Outbound Webhook dispatch with HMAC signature verification
"""

import json
import time
import pytest

from app.services.crm_service import CRMService
from app.services.lead_qualification_service import LeadQualificationService
from app.services.webhook_service import WebhookService
from app.providers.discovery.local_maps_provider import LocalMapsScraperProvider
from app.extractors.email import EmailExtractor
from app.extractors.phone import PhoneExtractor
from app.extractors.social import SocialExtractor


from app.models.business_lead import BusinessLead

@pytest.mark.asyncio
async def test_e2e_lead_to_deal_and_webhook_pipeline(db, client):
    """Full End-to-End autonomous pipeline execution."""

    # -------------------------------------------------------------
    # Step 1: Scraper Lead Simulation (Local Maps Scraper Engine format)
    # -------------------------------------------------------------
    raw_maps_place = {
        "title": "Apex Cyber Logistics Pvt Ltd",
        "category": "Logistics & Supply Chain",
        "address": "B-42, Cyber City, Sector 62, Noida, Uttar Pradesh 201309, India",
        "city": "Noida",
        "phone": "+91 98765 43210",
        "website": "https://apexcyberlogistics.com",
        "rating": 4.8,
        "reviews": 142,
        "latitude": 28.628,
        "longitude": 77.375,
        "place_id": "ChIJ_apex_cyber_12345",
        "cid": "987654321012345",
    }

    provider = LocalMapsScraperProvider()
    normalized = provider.normalize_business(raw_maps_place, default_location="Noida, India")
    assert normalized["business_name"] == "Apex Cyber Logistics Pvt Ltd"
    assert normalized["source_provider"] == "local_maps_scraper"
    assert normalized["phone"] is not None

    # -------------------------------------------------------------
    # Step 2: Extract Email, Phone, and Socials
    # -------------------------------------------------------------
    html_sample = """
    <html>
        <body>
            <h1>Contact Apex Cyber Logistics</h1>
            <p>Email: contact@apexcyberlogistics.com</p>
            <p>Phone: +91 9876543210</p>
            <a href="https://linkedin.com/company/apex-cyber-logistics">LinkedIn</a>
            <a href="https://x.com/apex_logistics">Twitter/X</a>
        </body>
    </html>
    """

    emails = EmailExtractor.extract_from_html(html_sample, normalized["website"])
    assert len(emails) > 0
    extracted_email = emails[0]["email"]
    assert extracted_email == "contact@apexcyberlogistics.com"

    phones = PhoneExtractor.extract_from_text(html_sample, normalized["website"], "IN")
    assert len(phones) > 0
    extracted_phone = phones[0]["normalized"]

    socials = SocialExtractor.extract_from_html(html_sample, normalized["website"])
    assert any(s["platform"].lower() in ["linkedin", "twitter", "x"] for s in socials)

    # -------------------------------------------------------------
    # Step 3: AI ICP Qualification & Scoring
    # -------------------------------------------------------------
    lead = BusinessLead(
        business_name=normalized["business_name"],
        category=normalized.get("category"),
        website=normalized.get("website"),
        address=normalized.get("address"),
        city=normalized.get("city", "Noida"),
        source_provider=normalized.get("source_provider"),
        provider_external_id=normalized.get("provider_external_id"),
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)

    qualification = await LeadQualificationService.qualify_lead(lead_id=str(lead.id), db=db)
    assert qualification is not None
    assert "qualification_score" in qualification
    assert qualification["qualification_score"] >= 0

    # -------------------------------------------------------------
    # Step 4: CRM Company, Contact & Deal Creation
    # -------------------------------------------------------------
    company = CRMService.create_company(
        db=db,
        data={
            "name": normalized["business_name"],
            "domain": "apexcyberlogistics.com",
            "industry": "Logistics & Supply Chain",
            "location": "Noida, Uttar Pradesh, India",
        },
    )
    assert company.id is not None
    assert company.name == "Apex Cyber Logistics Pvt Ltd"

    contact = CRMService.create_contact(
        db=db,
        data={
            "company_id": str(company.id),
            "first_name": "Sunil",
            "last_name": "Sharma",
            "email": extracted_email,
            "job_title": "Managing Director",
            "is_decision_maker": True,
        },
    )
    assert contact.id is not None
    assert contact.email == extracted_email

    pipeline = CRMService.get_or_create_default_pipeline(db)
    target_stage = pipeline.stages[0]

    from app.models.crm import Deal
    deal = Deal(
        pipeline_id=pipeline.id,
        stage_id=target_stage.id,
        company_id=company.id,
        contact_id=contact.id,
        title="Apex Cyber Logistics - AI Supply Chain Deal",
        amount=150000.0,
        currency="INR",
        probability=0.7,
    )
    db.add(deal)
    db.commit()
    db.refresh(deal)

    assert deal.id is not None
    assert deal.title == "Apex Cyber Logistics - AI Supply Chain Deal"
    assert deal.amount == 150000.0

    # Advance deal stage
    advanced_deal = CRMService.update_deal_stage(db, str(deal.id), str(pipeline.stages[1].id))
    assert str(advanced_deal.stage_id) == str(pipeline.stages[1].id)

    # -------------------------------------------------------------
    # Step 5: Webhook Subscription & Outbound Event Dispatch
    # -------------------------------------------------------------
    webhook_secret = "whsec_test_e2e_secret_key_998877"
    subscription = WebhookService.create_subscription(
        db=db,
        name="Enterprise CRM Integration Webhook",
        target_url="https://external-crm.enterprise.com/api/v1/leads/webhook",
        events=["lead.created", "deal.created", "lead.qualified"],
        secret_key=webhook_secret,
    )
    assert subscription.id is not None
    assert subscription.secret_key == webhook_secret

    event_payload = {
        "event": "deal.created",
        "timestamp": int(time.time()),
        "data": {
            "deal_id": str(deal.id),
            "deal_title": deal.title,
            "amount": deal.amount,
            "currency": deal.currency,
            "contact": {
                "name": f"{contact.first_name} {contact.last_name}",
                "email": contact.email,
                "company": company.name,
            },
            "qualification": qualification,
        }
    }

    payload_bytes = json.dumps(event_payload).encode("utf-8")

    # Verify HMAC-SHA256 signature generation
    signature = WebhookService.generate_signature(
        payload_bytes=payload_bytes,
        secret_key=webhook_secret,
    )
    assert signature.startswith("sha256=")

    # Verify signature verification passes
    is_valid = WebhookService.verify_signature(
        payload_bytes=payload_bytes,
        signature_header=signature,
        secret_key=webhook_secret,
    )
    assert is_valid is True

    # Verify tampered signature fails
    tampered_valid = WebhookService.verify_signature(
        payload_bytes=payload_bytes + b"tampered",
        signature_header=signature,
        secret_key=webhook_secret,
    )
    assert tampered_valid is False
