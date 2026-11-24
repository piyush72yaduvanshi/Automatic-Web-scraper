# AI Sales & CRM Operating System — REST API Specification

## 1. Overview & Authentication

All endpoints in the AI Sales & CRM Operating System are hosted under `/api/v1/` on the FastAPI server (default base URL: `http://localhost:8000`).

### Authentication
Security is enforced by constant-time string comparison (`backend/app/core/security.py`). When `AUTH_ENABLED=True` in environment configuration, requests must include the administrative key in one of two formats:
```http
X-API-Key: your_admin_api_key_here
```
or
```http
Authorization: Bearer your_admin_api_key_here
```
If omitted or invalid, the API returns:
```json
{
  "detail": "Invalid or missing API key"
}
```
*(Status: `401 Unauthorized`)*

---

## 2. API Endpoints by Domain

---

### 2.1. Centralized Integrations & Provider Health

#### `GET /api/v1/integrations`
Retrieves live health status across all 11 providers (AI, scrapers, communications, databases).
- **Response `200 OK`**:
```json
{
  "providers": [
    {
      "provider_name": "gemini",
      "status": "HEALTHY",
      "is_configured": true,
      "is_enabled": true,
      "last_success_at": "2026-11-03T02:45:10Z",
      "last_failure_at": null,
      "consecutive_failures": 0,
      "last_error_message": null,
      "details": { "model": "gemini-1.5-flash", "quota": "standard" }
    },
    {
      "provider_name": "gmail",
      "status": "CONFIGURED",
      "is_configured": true,
      "is_enabled": true,
      "last_success_at": null,
      "last_failure_at": null,
      "consecutive_failures": 0,
      "last_error_message": null,
      "details": { "mode": "oauth_live" }
    }
  ],
  "total": 11
}
```

#### `GET /api/v1/integrations/health`
Aggregated high-level health metrics for system health widgets.
- **Response `200 OK`**:
```json
{
  "overall_status": "HEALTHY",
  "total_providers": 11,
  "healthy": 9,
  "degraded": 1,
  "offline": 1,
  "disabled": 0
}
```

#### `POST /api/v1/integrations/{provider_name}/validate`
Triggers an immediate connection probe against a specific provider.
- **Path Parameters**: `provider_name` (`gemini`, `openrouter`, `serpapi`, `apify`, `firecrawl`, `gmail`, `whatsapp`, `database`, `redis`, `celery`)
- **Response `200 OK`**:
```json
{
  "provider": "gemini",
  "status": "HEALTHY",
  "message": "Connection probe succeeded (latency: 142ms)",
  "timestamp": "2026-11-03T02:48:00Z"
}
```

#### `POST /api/v1/integrations/{provider_name}/toggle`
Enables or disables a provider without requiring server restart.
- **Request Body**:
```json
{
  "is_enabled": false
}
```
- **Response `200 OK`**:
```json
{
  "provider": "openrouter",
  "is_enabled": false,
  "status": "DISABLED"
}
```

---

### 2.2. Lead Discovery & Scanners

#### `POST /api/v1/discovery/jobs`
Submits a background lead discovery job across maps and search directories.
- **Request Body**:
```json
{
  "query": "Solar panel installation contractors",
  "location": "Phoenix, AZ",
  "latitude": 33.4484,
  "longitude": -112.0740,
  "radius_km": 25.0,
  "max_results": 40
}
```
- **Response `201 Created`**:
```json
{
  "job_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "status": "pending",
  "query": "Solar panel installation contractors",
  "location": "Phoenix, AZ",
  "created_at": "2026-11-03T02:50:00Z"
}
```

#### `GET /api/v1/discovery/jobs/{job_id}`
Polls status and discovery counts for an active or completed job.
- **Response `200 OK`**:
```json
{
  "job_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "status": "completed",
  "total_found": 38,
  "created_at": "2026-11-03T02:50:00Z",
  "completed_at": "2026-11-03T02:51:15Z"
}
```

#### `GET /api/v1/discovery/stream/{job_id}`
Server-Sent Events (SSE) live stream yielding discovered lead records as they are parsed.
- **Headers**: `Accept: text/event-stream`
- **Output Format**: Continuous SSE event frames:
```text
event: lead_found
data: {"name": "Desert Sun Solar", "phone": "+1-602-555-0199", "website": "https://desertsunsolar.com"}
```

---

### 2.3. Lead Management, Qualification & Intelligence

#### `GET /api/v1/leads`
Lists discovered leads with filtering, search, and pagination.
- **Query Parameters**:
  - `search` (optional string): Keyword search in name or city
  - `status` (optional string): Filter by `new`, `contacted`, `converted`
  - `qualification_status` (optional string): `Qualified`, `Maybe`, `Rejected`, `New`
  - `limit` (integer, default 50)
  - `offset` (integer, default 0)
- **Response `200 OK`**:
```json
{
  "items": [
    {
      "id": "e4b3e839-a9a7-4b13-94cb-55d8d4745863",
      "name": "Desert Sun Solar",
      "city": "Phoenix",
      "state": "AZ",
      "phone": "+1-602-555-0199",
      "website": "https://desertsunsolar.com",
      "rating": 4.8,
      "qualification_score": 86.5,
      "qualification_status": "Qualified",
      "created_at": "2026-11-03T02:50:15Z"
    }
  ],
  "total": 1
}
```

#### `GET /api/v1/leads/{id}`
Returns complete lead record including contacts, social profiles, source evidence, and intelligence dossier.
- **Response `200 OK`**: Full `BusinessLead` schema with nested relations.

#### `POST /api/v1/leads/{id}/qualify`
Runs the AI Lead Qualification Engine evaluating the lead across 5 configurable ICP factors.
- **Request Body** (optional weight overrides):
```json
{
  "weights": {
    "icp_fit": 0.30,
    "pain_points": 0.25,
    "timing_intent": 0.20,
    "reachability": 0.15,
    "evidence_quality": 0.10
  }
}
```
- **Response `200 OK`**:
```json
{
  "lead_id": "e4b3e839-a9a7-4b13-94cb-55d8d4745863",
  "qualification_score": 88.0,
  "qualification_status": "Qualified",
  "reasoning": "Strong ICP fit for high-ticket commercial solar; active website with commercial contact information and high customer review presence.",
  "breakdown": {
    "icp_fit": 27.0,
    "pain_points": 22.5,
    "timing_intent": 16.0,
    "reachability": 13.5,
    "evidence_quality": 9.0
  },
  "recommended_action": "Draft personalized email outreach offering B2B lead generation audit."
}
```

#### `POST /api/v1/leads/{id}/research`
Executes deep digital footprint discovery and builds the structured Company Intelligence dossier.
- **Response `200 OK`**:
```json
{
  "lead_id": "e4b3e839-a9a7-4b13-94cb-55d8d4745863",
  "verified_facts": {
    "company_name": "Desert Sun Solar LLC",
    "verified_phone": "+1-602-555-0199",
    "address": "4100 N 24th St, Phoenix, AZ",
    "detected_technologies": ["WordPress", "Google Analytics", "Calendly"]
  },
  "inferred_insights": {
    "target_market": "High-volume residential & commercial installations",
    "potential_pain_points": ["Manual lead booking bottlenecks", "High CPC Google Ads cost"],
    "suggested_offering": "Automated inbound lead qualification and appointment routing"
  },
  "unknowns": [
    "Full-time employee count",
    "Exact monthly advertising spend",
    "Direct mobile for managing director"
  ]
}
```

#### `POST /api/v1/leads/{id}/feedback`
Records manual human score override and feedback with compliance audit logging.
- **Request Body**:
```json
{
  "score": 95.0,
  "status": "Qualified",
  "notes": "Verified directly via local industry association; high priority account."
}
```
- **Response `200 OK`**:
```json
{
  "lead_id": "e4b3e839-a9a7-4b13-94cb-55d8d4745863",
  "new_score": 95.0,
  "status": "Qualified",
  "audit_logged": true
}
```

#### `POST /api/v1/leads/manual`
Creates a new lead manually through the user interface.
- **Request Body**:
```json
{
  "name": "Apex Engineering",
  "website": "https://apex-eng.io",
  "phone": "+1-415-555-0182",
  "city": "San Francisco",
  "state": "CA",
  "category": "Structural Engineering"
}
```
- **Response `201 Created`**: Returns created `BusinessLead`.

#### `POST /api/v1/leads/import/csv`
Bulk imports leads from a user-supplied CSV file with deduplication.
- **Form Data**: `file` (multipart/form-data CSV)
- **Response `200 OK`**:
```json
{
  "total_rows": 120,
  "imported": 114,
  "duplicates_skipped": 6,
  "errors": []
}
```

---

### 2.4. Full Relational CRM Engine

#### `POST /api/v1/crm/companies/convert-from-lead/{lead_id}`
1-Click conversion promoting a discovered lead into a full CRM `Company`, creating an associated `Contact` and an open `Deal` in the default sales pipeline.
- **Response `201 Created`**:
```json
{
  "company": {
    "id": "c1f7b091-628d-4cb5-b44c-9f8fa1604a11",
    "name": "Desert Sun Solar",
    "domain": "desertsunsolar.com"
  },
  "contact": {
    "id": "d82efba1-381c-4b68-809f-e6eb20bdae03",
    "email": "contact@desertsunsolar.com"
  },
  "deal": {
    "id": "a931a292-628f-40f4-8a40-349f99bc7b2e",
    "title": "Desert Sun Solar — Inbound Automation",
    "amount": 5000.0,
    "status": "open"
  }
}
```

#### `GET /api/v1/crm/deals/kanban`
Retrieves pipeline stages and their grouped deals with total stage financial amounts.
- **Response `200 OK`**:
```json
{
  "stages": [
    {
      "id": "stage-uuid-1",
      "name": "Lead",
      "order_index": 0,
      "total_amount": 15000.0,
      "deals": [
        {
          "id": "a931a292-628f-40f4-8a40-349f99bc7b2e",
          "title": "Desert Sun Solar — Inbound Automation",
          "amount": 5000.0,
          "company_name": "Desert Sun Solar"
        }
      ]
    },
    {
      "id": "stage-uuid-2",
      "name": "Qualified",
      "order_index": 1,
      "total_amount": 28000.0,
      "deals": []
    }
  ]
}
```

#### `PUT /api/v1/crm/deals/{deal_id}/stage`
Transitions a deal to a new pipeline stage and logs an activity event.
- **Request Body**:
```json
{
  "stage_id": "stage-uuid-2",
  "status": "open"
}
```
- **Response `200 OK`**: Updated deal object.

#### `GET /api/v1/crm/companies` & `POST /api/v1/crm/companies`
Standard REST CRUD endpoints for CRM companies.

#### `GET /api/v1/crm/contacts` & `POST /api/v1/crm/contacts`
Standard REST CRUD endpoints for CRM contacts.

#### `GET /api/v1/crm/tasks` & `POST /api/v1/crm/tasks`
Creates and manages CRM tasks with priorities (`low`, `medium`, `high`, `urgent`) and due dates.

#### `PUT /api/v1/crm/tasks/{id}/complete`
Marks a task as completed.

#### `GET /api/v1/crm/meetings` & `POST /api/v1/crm/meetings`
Schedules sales calls with attendee links and AI-synthesized briefing notes.

---

### 2.5. AI Outreach Engine & Human Approval Queue

#### `GET /api/v1/outreach/approvals`
Lists outbound drafts awaiting human review.
- **Query Parameters**: `status` (optional string, defaults to `pending`)
- **Response `200 OK`**:
```json
{
  "items": [
    {
      "id": "673f4e10-388a-4c28-98f5-93df92d47aa1",
      "contact_id": "d82efba1-381c-4b68-809f-e6eb20bdae03",
      "channel": "email",
      "recipient_address": "contact@desertsunsolar.com",
      "subject": "Boosting Inbound Booking Conversion for Desert Sun Solar",
      "body_content": "Hi Team,\n\nI noticed Desert Sun Solar's impressive reviews in Phoenix...",
      "status": "pending",
      "created_at": "2026-11-03T03:00:00Z"
    }
  ],
  "total": 1
}
```

#### `POST /api/v1/outreach/approvals/{id}/approve`
Authorizes and immediately sends an outbound email or WhatsApp message.
- **Response `200 OK`**:
```json
{
  "id": "673f4e10-388a-4c28-98f5-93df92d47aa1",
  "status": "sent",
  "sent_at": "2026-11-03T03:02:10Z",
  "external_id": "gmail_msg_1928374a"
}
```

#### `POST /api/v1/outreach/approvals/{id}/reject`
Rejects a draft, preventing delivery and logging operator feedback.
- **Request Body**:
```json
{
  "reason": "Value proposition was too generic; needs mention of commercial roofing."
}
```
- **Response `200 OK`**:
```json
{
  "id": "673f4e10-388a-4c28-98f5-93df92d47aa1",
  "status": "rejected",
  "rejection_reason": "Value proposition was too generic; needs mention of commercial roofing."
}
```

#### `PUT /api/v1/outreach/approvals/{id}/edit`
Allows operator to modify draft text before sending.
- **Request Body**:
```json
{
  "subject": "New Subject Line",
  "body_content": "Updated body copy..."
}
```
- **Response `200 OK`**: Updated approval record.

#### `POST /api/v1/outreach/draft`
Prompts the Email Personalization Agent to draft a personalized message and stage it in the approval queue.
- **Request Body**:
```json
{
  "contact_id": "d82efba1-381c-4b68-809f-e6eb20bdae03",
  "channel": "email",
  "campaign_id": null
}
```
- **Response `201 Created`**: Created approval draft in `pending` state.

#### `GET /api/v1/outreach/suppression` & `POST /api/v1/outreach/suppression`
Manages the global suppression list. Any email or phone added here is blocked from outreach.

#### `GET /api/v1/outreach/conversations`
Retrieves threaded messaging histories across Gmail and WhatsApp.

---

### 2.6. Multi-Agent Orchestration & Telemetry

#### `GET /api/v1/agents`
Lists the 15 specialized agents, their descriptions, and registered tools.
- **Response `200 OK`**: Array of 15 agent descriptors.

#### `POST /api/v1/agents/{agent_name}/execute`
Directly invokes an individual specialized agent.
- **Request Body**:
```json
{
  "prompt": "Analyze lead Acme Corp and evaluate ICP fit.",
  "context": { "lead_id": "e4b3e839-a9a7-4b13-94cb-55d8d4745863" }
}
```
- **Response `200 OK`**:
```json
{
  "agent_name": "lead_qualification_agent",
  "provider_used": "gemini",
  "response": "Acme Corp demonstrates an ICP score of 88/100...",
  "tools_called": ["search_leads_db", "calculate_icp_score"],
  "execution_time_ms": 780.2
}
```

#### `POST /api/v1/agents/workflow`
Invokes the Master Orchestrator to decompose an objective into multi-step actions.
- **Request Body**:
```json
{
  "goal": "Discover 10 dental clinics in Austin, qualify them, and prepare outreach drafts."
}
```
- **Response `200 OK`**:
```json
{
  "workflow_id": "wf-849102",
  "total_steps": 3,
  "steps_completed": 3,
  "results": [
    { "step": 1, "agent": "lead_discovery_agent", "status": "completed" },
    { "step": 2, "agent": "lead_qualification_agent", "status": "completed" },
    { "step": 3, "agent": "email_personalization_agent", "status": "staged_for_approval" }
  ]
}
```

#### `GET /api/v1/agents/runs`
Returns telemetry execution logs across all agent invocations.

---

### 2.7. Knowledge Base & Hybrid RAG

#### `GET /api/v1/knowledge/documents` & `POST /api/v1/knowledge/documents`
Lists and uploads documents (playbooks, offerings, case studies) for semantic indexing.

#### `POST /api/v1/knowledge/search`
Hybrid vector cosine similarity + lexical keyword search.
- **Request Body**:
```json
{
  "query": "pricing model for outbound sales automation",
  "top_k": 3
}
```
- **Response `200 OK`**:
```json
{
  "results": [
    {
      "document_id": "doc-uuid-1",
      "document_title": "Agency Pricing & Packaging Playbook",
      "chunk_text": "Our outbound automation retainer begins at $3,500/month...",
      "score": 0.89
    }
  ]
}
```

---

### 2.8. Calculated Business Analytics

#### `GET /api/v1/analytics/overview`
Returns real computed business KPIs computed directly from database records.
- **Response `200 OK`**:
```json
{
  "leads": {
    "total": 154,
    "qualified": 42,
    "rejected": 12,
    "avg_score": 74.2
  },
  "pipeline": {
    "open_deals": 18,
    "open_value": 92500.0,
    "won_deals": 5,
    "won_value": 24000.0,
    "win_rate_percent": 21.7
  },
  "operations": {
    "pending_approvals": 6,
    "tasks_due": 4,
    "meetings_scheduled": 3
  },
  "ai_telemetry": {
    "total_agent_runs": 87,
    "success_rate_percent": 98.8,
    "avg_execution_ms": 640.5
  }
}
```
