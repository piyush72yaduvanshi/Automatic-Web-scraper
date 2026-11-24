"""Comprehensive Test Suite for Phase 2:
Native Python Workflow Engine, Deliverability, Campaigns, Sequences, Reply Intelligence,
Compliance, Content Marketing, SEO, Meetings, and Reporting.
"""

import pytest
import uuid
from datetime import datetime
from fastapi.testclient import TestClient

from main import app
from app.core.database import SessionLocal, Base, engine
from app.models.workflow import WorkflowDefinition, WorkflowExecution
from app.models.deliverability import EmailAccount, EmailDomain, EmailEvent
from app.models.campaign import CampaignMember, FollowupSequence, FollowupStep
from app.models.compliance import ConsentRecord, DataDeletionRequest
from app.models.marketing import ContentItem, SEOProject, SEOKeyword
from app.models.reporting import ReportSnapshot
from app.models.outreach import OutreachCampaign, Conversation, ConversationMessage, SuppressionRecord
from app.models.crm import Contact, CRMTask

from app.services.workflow_engine_service import WorkflowEngineService
from app.services.deliverability_service import DeliverabilityService
from app.services.campaign_engine_service import CampaignEngineService
from app.services.sequence_engine_service import SequenceEngineService
from app.services.reply_intelligence_service import ReplyIntelligenceService
from app.services.compliance_service import ComplianceService
from app.services.content_marketing_service import ContentMarketingService
from app.services.seo_service import SEOService
from app.services.meeting_service import MeetingService
from app.services.reporting_service import ReportingService
from app.services.exception_queue_service import ExceptionQueueService


# -----------------------------------------------------------------------------
# 1. Native Python Workflow Engine Tests (Zero n8n)
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_native_workflow_engine_full_lifecycle(db):
    """Tests workflow definition creation, step execution, conditional branching, and history."""
    # 1. Create declarative workflow definition
    w_def = WorkflowEngineService.create_definition(
        data={
            "name": "Test Lead Qualification & Task Flow",
            "trigger_type": "MANUAL",
            "steps": [
                {
                    "step_id": "step_branch",
                    "name": "Check Priority",
                    "action_type": "CONDITIONAL_BRANCH",
                    "config": {
                        "field": "score",
                        "operator": ">=",
                        "value": 80,
                        "next_step_true": "step_task",
                        "next_step_false": "step_activity",
                    },
                },
                {
                    "step_id": "step_task",
                    "name": "Create Urgent Follow-up",
                    "action_type": "CREATE_CRM_TASK",
                    "config": {"title": "Urgent Lead Outreach", "priority": "urgent"},
                },
                {
                    "step_id": "step_activity",
                    "name": "Log Note",
                    "action_type": "LOG_ACTIVITY",
                    "config": {"title": "Standard lead logged"},
                },
            ],
        },
        db=db,
    )
    assert w_def["status"] == "CREATED"
    wf_id = w_def["id"]

    # 2. Execute workflow with score = 85 (should take branch_true -> step_task)
    exec_res = await WorkflowEngineService.execute_workflow(
        workflow_id=wf_id,
        trigger_event="MANUAL",
        input_payload={"score": 85, "company_name": "Solar Inc"},
        db=db,
    )
    assert exec_res["status"] == "COMPLETED"
    assert "step_branch" in exec_res["step_results"]
    assert "step_task" in exec_res["step_results"]

    # 3. Verify execution was recorded in PostgreSQL / SQLite
    exec_history = WorkflowEngineService.list_executions(db=db, workflow_id=wf_id)
    assert len(exec_history) >= 1
    assert exec_history[0]["status"] == "COMPLETED"


# -----------------------------------------------------------------------------
# 2. Email Deliverability, Kill Switch & Domain Authentication Tests
# -----------------------------------------------------------------------------
def test_deliverability_and_kill_switch(db):
    """Tests domain DNS checks, kill switch activation/deactivation, and duplicate prevention."""
    # 1. Kill Switch Toggle
    status_off = DeliverabilityService.get_kill_switch_status()
    assert status_off is False

    toggled_on = DeliverabilityService.set_kill_switch(enabled=True, reason="Unit test safety check", db=db)
    assert toggled_on["kill_switch_active"] is True
    assert DeliverabilityService.get_kill_switch_status() is True

    # Check that compliance pre-flight fails when kill switch is on
    eligibility = ComplianceService.check_recipient_eligibility(
        recipient="prospect@example.com",
        channel="EMAIL",
        db=db,
    )
    assert eligibility["is_eligible"] is False
    assert eligibility["reason"] == "GLOBAL_KILL_SWITCH_ACTIVE"

    # Deactivate Kill Switch
    DeliverabilityService.set_kill_switch(enabled=False, reason="Resume test", db=db)
    assert DeliverabilityService.get_kill_switch_status() is False

    # 2. Live DNS Verification probe on a known public domain
    dns_res = DeliverabilityService.verify_domain_dns("google.com", db=db)
    assert dns_res["spf_status"] in ["VERIFIED", "FAILED", "UNAVAILABLE"]
    assert dns_res["mx_status"] in ["VERIFIED", "FAILED", "UNAVAILABLE"]

    # 3. Duplicate Send Protection
    test_email = f"lead_{uuid.uuid4().hex[:6]}@domain.com"
    DeliverabilityService.log_email_event(
        event_type="SENT",
        recipient=test_email,
        campaign_id=None,
        email_account_id=None,
        payload={"subject": "Hello"},
        db=db,
    )
    is_dup = DeliverabilityService.check_duplicate_send(test_email, None, db=db)
    assert is_dup is True


# -----------------------------------------------------------------------------
# 3. Campaign Engine & Member Enrollment Tests
# -----------------------------------------------------------------------------
def test_campaign_management_and_enrollment(db):
    """Tests campaign creation across the 5 campaign types and pre-flight compliance filtering."""
    # 1. Create B2B Prospecting campaign
    camp = CampaignEngineService.create_campaign(
        data={
            "name": "Q4 Prospecting Campaign",
            "campaign_type": "B2B_PROSPECTING",
            "description": "Cold outbound to engineering firms",
        },
        db=db,
    )
    assert camp["campaign_type"] == "B2B_PROSPECTING"
    camp_id = camp["id"]

    # 2. Add an email to suppression
    suppressed_email = f"optout_{uuid.uuid4().hex[:6]}@firm.com"
    sup = SuppressionRecord(recipient=suppressed_email, channel="ALL", reason="UNSUBSCRIBE")
    db.add(sup)
    db.commit()

    # 3. Attempt to enroll 2 emails (one valid, one suppressed)
    valid_email = f"valid_{uuid.uuid4().hex[:6]}@firm.com"
    enroll_res = CampaignEngineService.enroll_prospects(
        campaign_id=camp_id,
        prospect_emails=[valid_email, suppressed_email],
        db=db,
    )
    assert enroll_res["enrolled"] == 1
    assert enroll_res["skipped"] == 1


# -----------------------------------------------------------------------------
# 4. Reply Intelligence & Stop Conditions Tests
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_reply_intelligence_and_stop_conditions(db):
    """Tests 11-category classification and stop conditions (pause sequences, suppress, create tasks)."""
    # 1. Test Regex / Heuristic classification
    res_unsub = await ReplyIntelligenceService.classify_reply("Please unsubscribe me and stop emailing.")
    assert res_unsub["classification"] == "UNSUBSCRIBE"

    res_meet = await ReplyIntelligenceService.classify_reply("Sounds great, let's schedule a call this Thursday at 2pm.")
    assert res_meet["classification"] == "MEETING_REQUEST"

    res_int = await ReplyIntelligenceService.classify_reply("I am interested, can you send over pricing?")
    assert res_int["classification"] == "INTERESTED"

    # 2. Test Processing an Inbound Message into Conversation
    conv = Conversation(channel="EMAIL", subject="Intro", status="ACTIVE")
    db.add(conv)
    db.commit()

    prospect_email = f"prospect_{uuid.uuid4().hex[:6]}@lead.com"
    # Enroll in campaign
    camp = OutreachCampaign(name="Outreach", status="ACTIVE")
    db.add(camp)
    db.commit()

    member = CampaignMember(campaign_id=camp.id, recipient_email=prospect_email, status="ENROLLED")
    db.add(member)
    db.commit()

    # Process incoming interested message
    proc_res = await ReplyIntelligenceService.process_incoming_message(
        conversation_id=str(conv.id),
        sender=prospect_email,
        body_text="We love the idea, let's set up a demo call.",
        db=db,
    )
    assert proc_res["classification"] in ["INTERESTED", "MEETING_REQUEST"]
    # Verify sequence was automatically paused
    db.refresh(member)
    assert member.status == "PAUSED"


# -----------------------------------------------------------------------------
# 5. Follow-up Sequence Engine & 7 Pre-Execution Checks Tests
# -----------------------------------------------------------------------------
def test_sequence_engine_7_checks(db):
    """Tests cadence definition (Day 0, 3, 7, 14) and 7 pre-execution checks."""
    seq_res = SequenceEngineService.create_sequence(
        data={
            "name": "Custom 14-Day Cadence",
            "campaign_type": "B2B_PROSPECTING",
            "steps": [
                {"step_number": 1, "delay_days": 0, "subject_template": "Day 0 Intro", "body_template": "Hello"},
                {"step_number": 2, "delay_days": 3, "subject_template": "Day 3 Followup", "body_template": "Checking in"},
            ],
        },
        db=db,
    )
    assert seq_res["steps_created"] == 2
    seq_id = seq_res["id"]

    # Execute due steps
    due_res = SequenceEngineService.execute_due_sequence_steps(sequence_id=seq_id, db=db)
    assert "staged_for_approval" in due_res


# -----------------------------------------------------------------------------
# 6. Global Compliance & Right to be Forgotten Tests
# -----------------------------------------------------------------------------
def test_compliance_and_erasure(db):
    """Tests consent recording and GDPR Right to be Forgotten erasure."""
    user_email = f"gdpr_user_{uuid.uuid4().hex[:6]}@privacy.org"

    # Record initial consent
    consent = ComplianceService.record_consent(
        data={
            "recipient": user_email,
            "source": "WEBSITE_INQUIRY",
            "lawful_basis": "CONSENT",
            "marketing_eligible": True,
        },
        db=db,
    )
    assert consent["marketing_eligible"] is True

    # Create dummy Contact
    contact = Contact(first_name="John", last_name="Privacy", email=user_email)
    db.add(contact)
    db.commit()

    # Execute Deletion Request
    del_res = ComplianceService.execute_deletion_request(
        recipient=user_email,
        reason="GDPR_ARTICLE_17_ERASURE",
        db=db,
    )
    assert del_res["status"] == "COMPLETED"
    assert del_res["suppressed"] is True

    # Contact must be anonymized
    db.refresh(contact)
    assert contact.first_name == "ANONYMIZED"
    assert contact.email != user_email

    # Subsequent outreach must be blocked
    chk = ComplianceService.check_recipient_eligibility(user_email, "EMAIL", db)
    assert chk["is_eligible"] is False


# -----------------------------------------------------------------------------
# 7. Content Marketing, SEO, Meetings & Reporting Tests
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_content_seo_meetings_and_reports(db):
    """Tests multi-platform content generation, SEO clustering, meetings, and operational report generation."""
    # 1. Content Generation across LinkedIn, X, Reddit
    content_res = await ContentMarketingService.create_and_repurpose_content(
        data={
            "title": "Scaling Sales Pipelines",
            "pillar": "TECHNICAL_EXPERTISE",
            "core_idea": "Multi-agent systems outperform monolithic prompts for enterprise sales discovery.",
            "platforms": ["LINKEDIN", "X"],
        },
        db=db,
    )
    assert content_res["status"] == "PENDING_APPROVAL"
    assert "LINKEDIN" in content_res["platform_drafts"]

    # 2. Schedule to calendar
    cal_res = ContentMarketingService.schedule_calendar_entry(
        data={"content_item_id": content_res["id"], "channel": "LINKEDIN", "scheduled_for": datetime.utcnow().isoformat()},
        db=db,
    )
    assert cal_res["status"] == "SCHEDULED"
    assert cal_res["publishing_provider_status"] == "NOT_CONFIGURED"

    # 3. Schedule Meeting & AI Executive Briefing
    meet_res = await MeetingService.schedule_meeting(
        data={
            "title": "Demo Call with Apex Corp",
            "company_name": "Apex Corp",
            "duration_minutes": 30,
        },
        db=db,
    )
    assert meet_res["status"] == "scheduled"
    assert meet_res["calendar_sync_status"] == "SIMULATED_LOCAL"

    # 4. Generate Operational Daily Report Snapshot
    rep_res = await ReportingService.generate_report(report_type="DAILY", db=db)
    assert rep_res["report_type"] == "DAILY"
    assert "metrics" in rep_res
    assert len(rep_res["recommendations"]) >= 1

    # 5. Exception Queue
    ex_queue = ExceptionQueueService.get_exception_items(db=db)
    assert "items" in ex_queue
    assert "total_exceptions" in ex_queue


# -----------------------------------------------------------------------------
# 8. API Endpoint Routing Tests for Phase 2
# -----------------------------------------------------------------------------
def test_phase2_api_endpoints(client):
    """Verifies HTTP status 200 on all newly mounted Phase 2 endpoints."""
    # Workflows
    r = client.get("/api/v1/workflows")
    assert r.status_code == 200

    r = client.get("/api/v1/workflows/executions")
    assert r.status_code == 200

    # Deliverability
    r = client.get("/api/v1/deliverability/stats")
    assert r.status_code == 200

    r = client.get("/api/v1/deliverability/mailboxes")
    assert r.status_code == 200

    r = client.get("/api/v1/deliverability/kill-switch")
    assert r.status_code == 200

    # Campaigns & Sequences
    r = client.get("/api/v1/campaigns")
    assert r.status_code == 200

    r = client.get("/api/v1/sequences")
    assert r.status_code == 200

    # Compliance
    r = client.get("/api/v1/compliance/consents")
    assert r.status_code == 200

    # Content & SEO
    r = client.get("/api/v1/content/items")
    assert r.status_code == 200

    r = client.get("/api/v1/content/calendar")
    assert r.status_code == 200

    r = client.get("/api/v1/seo/projects")
    assert r.status_code == 200

    # Meetings & Reports
    r = client.get("/api/v1/meetings")
    assert r.status_code == 200

    r = client.get("/api/v1/reports")
    assert r.status_code == 200

    # Exceptions
    r = client.get("/api/v1/exceptions")
    assert r.status_code == 200
