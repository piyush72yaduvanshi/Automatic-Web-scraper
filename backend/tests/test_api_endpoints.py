"""Integration tests for all newly added API endpoints."""

import pytest
from fastapi.testclient import TestClient


def test_integrations_endpoints(client: TestClient):
    # GET /api/v1/integrations
    resp = client.get("/api/v1/integrations")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 9

    # GET /api/v1/integrations/health
    resp_health = client.get("/api/v1/integrations/health")
    assert resp_health.status_code == 200
    health_data = resp_health.json()
    assert "overall_status" in health_data
    assert "healthy_count" in health_data


def test_agents_endpoints(client: TestClient):
    # GET /api/v1/agents
    resp = client.get("/api/v1/agents")
    assert resp.status_code == 200
    agents = resp.json()
    assert len(agents) == 15

    # POST /api/v1/agents/lead_discovery_agent/execute
    exec_resp = client.post(
        "/api/v1/agents/lead_discovery_agent/execute",
        json={"query": "Dentist", "location": "Lucknow"},
    )
    assert exec_resp.status_code == 200
    result = exec_resp.json()
    assert result["success"] is True
    assert "result" in result


def test_crm_endpoints(client: TestClient):
    # POST /api/v1/crm/companies
    c_resp = client.post(
        "/api/v1/crm/companies",
        json={"name": "Test Hospital", "industry": "Healthcare", "location": "Lucknow"},
    )
    assert c_resp.status_code == 200
    company_id = c_resp.json()["id"]

    # GET /api/v1/crm/companies
    list_resp = client.get("/api/v1/crm/companies")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 1

    # POST /api/v1/crm/contacts
    ct_resp = client.post(
        "/api/v1/crm/contacts",
        json={
            "company_id": company_id,
            "first_name": "Priya",
            "last_name": "Verma",
            "email": "priya@testhospital.org",
            "job_title": "Medical Director",
            "is_decision_maker": True,
        },
    )
    assert ct_resp.status_code == 200

    # GET /api/v1/crm/deals/kanban
    kanban_resp = client.get("/api/v1/crm/deals/kanban")
    assert kanban_resp.status_code == 200
    assert "stages" in kanban_resp.json()


def test_outreach_endpoints(client: TestClient):
    # GET /api/v1/outreach/approvals
    resp = client.get("/api/v1/outreach/approvals")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)

    # POST /api/v1/outreach/suppression
    supp_resp = client.post(
        "/api/v1/outreach/suppression",
        json={"recipient": "optout@example.com", "channel": "EMAIL", "reason": "UNSUBSCRIBE"},
    )
    assert supp_resp.status_code == 200
    assert supp_resp.json()["status"] == "suppressed"


def test_knowledge_endpoints(client: TestClient):
    # POST /api/v1/knowledge/documents
    doc_resp = client.post(
        "/api/v1/knowledge/documents",
        json={
            "title": "Software Agency Playbook",
            "category": "SERVICE_OFFERING",
            "content": "We offer custom ERP and CRM solutions for growing businesses in India and global markets.",
        },
    )
    assert doc_resp.status_code == 200
    assert doc_resp.json()["status"] == "created"

    # POST /api/v1/knowledge/search
    search_resp = client.post(
        "/api/v1/knowledge/search",
        json={"query": "ERP and CRM solutions", "limit": 3},
    )
    assert search_resp.status_code == 200
    assert "results" in search_resp.json()


def test_analytics_endpoints(client: TestClient):
    # GET /api/v1/analytics/overview
    resp = client.get("/api/v1/analytics/overview")
    assert resp.status_code == 200
    data = resp.json()
    assert "leads" in data
    assert "pipeline" in data
    assert "tasks_and_calendar" in data
    assert "ai_telemetry" in data
