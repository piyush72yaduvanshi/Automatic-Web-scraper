"""Comprehensive tests for CRM, Specialized Agents, Outreach Approvals, and Knowledge Base."""

import pytest
from app.services.crm_service import CRMService
from app.services.outreach_service import OutreachService
from app.services.knowledge_service import KnowledgeService
from app.services.lead_qualification_service import LeadQualificationService
from app.services.company_intelligence_service import CompanyIntelligenceService
from app.services.analytics_service import AnalyticsService
from app.ai.agents.specialized import AgentRegistry
from app.ai.orchestrator.orchestrator import AIOrchestrator
from app.models.business_lead import BusinessLead


def test_agent_registry_all_15_agents():
    agents = AgentRegistry.list_agents()
    assert len(agents) == 15
    names = {a["name"] for a in agents}
    assert "lead_discovery_agent" in names
    assert "company_research_agent" in names
    assert "lead_qualification_agent" in names
    assert "email_personalization_agent" in names
    assert "workflow_planning_agent" in names
    assert "reply_classification_agent" in names
    assert "crm_management_agent" in names


def test_crm_core_operations(db):
    # 1. Company creation
    company = CRMService.create_company(
        db=db,
        data={
            "name": "Apex Software Systems",
            "domain": "apexsoftware.io",
            "industry": "Information Technology",
            "location": "Lucknow, India",
        },
    )
    assert company.id is not None
    assert company.name == "Apex Software Systems"

    # 2. Contact creation
    contact = CRMService.create_contact(
        db=db,
        data={
            "company_id": str(company.id),
            "first_name": "Rohan",
            "last_name": "Sharma",
            "email": "rohan@apexsoftware.io",
            "job_title": "CTO",
            "is_decision_maker": True,
        },
    )
    assert contact.id is not None
    assert contact.first_name == "Rohan"

    # 3. Pipeline & Deals
    pipeline = CRMService.get_or_create_default_pipeline(db)
    assert len(pipeline.stages) >= 6

    deal = CRMService.create_company(
        db=db,
        data={"name": "Deal Target Inc"},
    )
    kanban = CRMService.get_kanban_board(db)
    assert "stages" in kanban
    assert len(kanban["stages"]) >= 6

    # 4. Tasks & Activities
    task = CRMService.create_task(
        db=db,
        data={
            "title": "Send technical architecture proposal",
            "priority": "high",
            "company_id": str(company.id),
        },
    )
    assert task.status == "pending"
    completed = CRMService.complete_task(db, str(task.id))
    assert completed.status == "completed"

    timeline = CRMService.get_timeline(db, company_id=str(company.id))
    assert len(timeline) >= 1


@pytest.mark.asyncio
async def test_lead_qualification_and_research(db, sample_business_data):
    lead = BusinessLead(**sample_business_data)
    db.add(lead)
    db.commit()
    db.refresh(lead)

    # Qualification
    qual_res = await LeadQualificationService.qualify_lead(lead_id=str(lead.id), db=db)
    assert "qualification_score" in qual_res
    assert qual_res["qualification_score"] >= 0
    assert qual_res["qualification_status"] in LeadQualificationService.VALID_STATUSES

    # Manual feedback override
    feedback_res = LeadQualificationService.apply_manual_feedback(
        lead_id=str(lead.id),
        new_score=85.0,
        new_status="Qualified",
        reason="Verified active budget and verified CEO email",
        db=db,
    )
    assert feedback_res["qualification_score"] == 85.0
    assert feedback_res["qualification_status"] == "Qualified"

    # Research
    research_res = await CompanyIntelligenceService.analyze_company(lead_id=str(lead.id), db=db)
    assert "verified_facts" in research_res
    assert "inferred_insights" in research_res
    assert "unknowns" in research_res


@pytest.mark.asyncio
async def test_human_approval_queue_and_suppression(db, sample_business_data):
    lead = BusinessLead(**sample_business_data)
    db.add(lead)
    db.commit()
    db.refresh(lead)

    # 1. AI prepares draft -> must go into PENDING queue
    draft = await OutreachService.prepare_outreach_draft_for_lead(
        lead_id=str(lead.id),
        channel="EMAIL",
        db=db,
    )
    assert draft.status == "PENDING"
    assert draft.recipient_destination is not None

    # 2. User approves and sends
    res = await OutreachService.approve_and_send(str(draft.id), db)
    assert res["success"] is True

    # 3. Suppression check
    suppressed = OutreachService.add_to_suppression(
        recipient="unsub@testbusiness.com",
        channel="ALL",
        reason="UNSUBSCRIBE",
        db=db,
    )
    assert OutreachService.is_suppressed("unsub@testbusiness.com", "EMAIL", db) is True
    assert OutreachService.is_suppressed("allowed@testbusiness.com", "EMAIL", db) is False


@pytest.mark.asyncio
async def test_knowledge_base_rag(db):
    doc = await KnowledgeService.create_document(
        title="Custom CRM Engineering Playbook",
        content="Our primary service is high-performance Python FastAPI and React sales automation platforms. We specialize in AI agents, WhatsApp integration, and PostgreSQL multi-channel leads.",
        category="SERVICE_OFFERING",
        db=db,
    )
    assert doc.id is not None
    assert len(doc.chunks) >= 1

    search_res = await KnowledgeService.search_knowledge("FastAPI React sales platform", limit=3, db=db)
    assert len(search_res) >= 1
    assert "FastAPI" in search_res[0]["chunk_text"]


@pytest.mark.asyncio
async def test_autonomous_workflow_orchestration(db):
    result = await AIOrchestrator.run_autonomous_workflow(
        user_goal="Find software agencies and prepare introductory outreach",
        db=db,
        auto_execute_safe_steps=True,
    )
    assert "workflow_name" in result
    assert result["total_steps"] >= 1
    assert len(result["execution_log"]) >= 1


def test_analytics_computation(db):
    overview = AnalyticsService.get_dashboard_overview(db)
    assert "leads" in overview
    assert "pipeline" in overview
    assert "tasks_and_calendar" in overview
    assert "ai_telemetry" in overview
    assert overview["ai_telemetry"]["total_agent_runs"] >= 0

