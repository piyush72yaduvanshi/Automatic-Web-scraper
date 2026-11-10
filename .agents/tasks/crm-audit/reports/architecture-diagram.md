# CRM System Architecture Documentation

**Version:** 2.5.0  
**Last Updated:** November 10, 2026  
**System:** AI Sales & CRM Lead Discovery Platform

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Component Interactions](#component-interactions)
4. [Data Flow](#data-flow)
5. [Integration Points](#integration-points)
6. [Technology Stack](#technology-stack)
7. [Deployment Architecture](#deployment-architecture)

---

## System Overview

The AI Sales & CRM Lead Discovery Platform is an enterprise-grade system for automated lead discovery, AI-powered qualification, multi-channel outreach, and CRM management. The system follows a modern microservices-inspired architecture with clear separation between presentation, business logic, and data layers.

### Key Characteristics

- **Architecture Pattern:** Layered monolith with service-oriented design
- **API Design:** RESTful with OpenAPI/Swagger documentation
- **Data Storage:** PostgreSQL with pgvector for semantic search
- **Caching Layer:** Redis for rate limiting and background jobs
- **Object Storage:** MinIO S3-compatible for media assets
- **Frontend:** Single-page application with code splitting
- **Background Processing:** Celery for long-running tasks

---

## Architecture Diagram

### High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│   ┌───────────────────────────────────────────────────────────┐    │
│   │        React Frontend (Port 3000/5173)                     │    │
│   │  - React 18 + TypeScript + Vite                           │    │
│   │  - TanStack Query (API caching)                           │    │
│   │  - Tailwind CSS + Lucide icons                            │    │
│   │  - Code splitting + lazy loading                          │    │
│   │  - Sentry error tracking                                  │    │
│   └─────────────────┬─────────────────────────────────────────┘    │
│                     │                                                │
│                     │ HTTP/REST                                      │
│                     ▼                                                │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                      APPLICATION LAYER                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│   ┌───────────────────────────────────────────────────────────┐    │
│   │       FastAPI Backend (Port 8000)                          │    │
│   │  ┌─────────────────────────────────────────────────────┐  │    │
│   │  │  API Routes (24 modules)                            │  │    │
│   │  │  - health, discovery, leads, crm, agents            │  │    │
│   │  │  - outreach, workflows, campaigns, etc.             │  │    │
│   │  └──────────────────┬──────────────────────────────────┘  │    │
│   │                     │                                       │    │
│   │  ┌─────────────────▼──────────────────────────────────┐  │    │
│   │  │  Business Services (25 modules)                     │  │    │
│   │  │  - Discovery, enrichment, qualification             │  │    │
│   │  │  - Outreach orchestration, CRM management           │  │    │
│   │  │  - AI agent coordination, knowledge retrieval       │  │    │
│   │  └──────────────────┬──────────────────────────────────┘  │    │
│   │                     │                                       │    │
│   │  ┌─────────────────▼──────────────────────────────────┐  │    │
│   │  │  AI Agent Layer (15 specialized agents)            │  │    │
│   │  │  - Lead discovery, company research                │  │    │
│   │  │  - Qualification, outreach strategy                │  │    │
│   │  │  - Email personalization, reply classification     │  │    │
│   │  └──────────────────┬──────────────────────────────────┘  │    │
│   │                     │                                       │    │
│   │  ┌─────────────────▼──────────────────────────────────┐  │    │
│   │  │  Provider Abstraction Layer                         │  │    │
│   │  │  - Discovery providers (Apify, SerpAPI, Places)    │  │    │
│   │  │  - AI providers (Gemini, OpenRouter, Heuristic)    │  │    │
│   │  │  - Enrichment (Firecrawl, extractors)              │  │    │
│   │  │  - Communication (Gmail, WhatsApp, Social)         │  │    │
│   │  └─────────────────────────────────────────────────────┘  │    │
│   └───────────────────────────────────────────────────────────┘    │
│                                                                       │
│   ┌───────────────────────────────────────────────────────────┐    │
│   │       Celery Worker (Background Jobs)                      │    │
│   │  - Discovery job execution                                 │    │
│   │  - Enrichment processing                                   │    │
│   │  - Campaign execution                                      │    │
│   │  - Concurrency: 2 workers                                 │    │
│   └───────────────────────────────────────────────────────────┘    │
│                                                                       │
└────────┬──────────────────────────────────────┬────────────┬────────┘
         │                                       │            │
         ▼                                       ▼            ▼

┌─────────────────────────────────────────────────────────────────────┐
│                         DATA LAYER                                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌──────────────────┐  ┌──────────────────┐  ┌─────────────────┐  │
│  │   PostgreSQL 16  │  │     Redis 7      │  │   MinIO S3      │  │
│  │   (Port 5432)    │  │   (Port 6379)    │  │  (Port 9000)    │  │
│  │                  │  │                  │  │                 │  │
│  │  - pgvector ext  │  │  - Rate limiting │  │  - Images       │  │
│  │  - 17 tables     │  │  - Celery queue  │  │  - Documents    │  │
│  │  - 59 indexes    │  │  - Cache store   │  │  - Creatives    │  │
│  │  - 768-dim vect  │  │                  │  │                 │  │
│  └──────────────────┘  └──────────────────┘  └─────────────────┘  │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                   EXTERNAL INTEGRATIONS                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Lead Discovery:  AI Services:     Communication:    Social Media:   │
│  • Apify         • Gemini Flash    • Gmail OAuth2    • Instagram    │
│  • SerpAPI       • OpenRouter      • WhatsApp Meta   • Facebook     │
│  • Google Places • Embeddings      • SMS providers   • Twitter/X    │
│                                                       • LinkedIn     │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                   OBSERVABILITY LAYER                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Error Tracking:  Metrics:          Health Checks:   Logging:        │
│  • Sentry        • Prometheus       • /api/v1/health • JSON format   │
│  • Frontend      • /metrics endpoint• All services   • Request IDs   │
│  • Backend       • Request duration • Docker health  • Structured    │
│                  • Status codes                                       │
└─────────────────────────────────────────────────────────────────────┘
```

### Backend Service Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │            Middleware Stack                         │    │
│  │  1. CORS (conditional: production vs development)  │    │
│  │  2. Security Headers (6 headers)                   │    │
│  │  3. Request ID generation (UUID)                   │    │
│  │  4. Rate Limiter (slowapi + Redis)                 │    │
│  │  5. Exception handlers (validation, unhandled)     │    │
│  └────────────────────────────────────────────────────┘    │
│                           │                                  │
│                           ▼                                  │
│  ┌────────────────────────────────────────────────────┐    │
│  │              API Router (v1)                        │    │
│  │  /api/v1/health      - Health checks               │    │
│  │  /api/v1/discovery   - Lead discovery jobs         │    │
│  │  /api/v1/leads       - Business leads CRUD         │    │
│  │  /api/v1/crm/*       - Companies, contacts, deals  │    │
│  │  /api/v1/agents      - AI agent execution          │    │
│  │  /api/v1/outreach    - Approval + send workflows   │    │
│  │  /api/v1/workflows   - Workflow engine             │    │
│  │  /api/v1/campaigns   - Campaign management         │    │
│  │  /api/v1/knowledge   - RAG knowledge base          │    │
│  │  ... (24 total route modules)                      │    │
│  └────────────────────────────────────────────────────┘    │
│                           │                                  │
│                           ▼                                  │
│  ┌────────────────────────────────────────────────────┐    │
│  │           Business Logic Services                   │    │
│  │                                                     │    │
│  │  DiscoveryService       - Multi-source orchestr.   │    │
│  │  EnrichmentService      - Website scraping         │    │
│  │  QualificationService   - Lead scoring             │    │
│  │  OutreachService        - Multi-channel send       │    │
│  │  CRMService             - Pipeline management      │    │
│  │  AgentOrchestratorSvc   - AI agent coordination    │    │
│  │  KnowledgeService       - RAG retrieval            │    │
│  │  StorageService         - MinIO object storage     │    │
│  │  ... (25 service modules)                          │    │
│  └────────────────────────────────────────────────────┘    │
│                           │                                  │
│                           ▼                                  │
│  ┌────────────────────────────────────────────────────┐    │
│  │            Data Access Layer                        │    │
│  │  SQLAlchemy 2.0 ORM                                │    │
│  │  - 17 model classes                                │    │
│  │  - Async session support                           │    │
│  │  - Connection pooling (20 + 10 overflow)          │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Interactions

### 1. Lead Discovery Flow

```
User (Frontend)
    │
    │ POST /api/v1/discovery/jobs
    │ { query: "restaurants", location: "New York", provider: "apify" }
    ▼
FastAPI Backend
    │
    │ Validate request (Pydantic)
    │ Check rate limit (10/min)
    ▼
DiscoveryService
    │
    │ Create DiscoveryJob record
    │ Enqueue Celery task
    ▼
Celery Worker
    │
    │ Select provider (Apify/SerpAPI/GooglePlaces)
    ▼
Provider (e.g., Apify)
    │
    │ Execute actor: Google Maps Scraper
    │ Wait for results (300s timeout)
    ▼
Enrichment Pipeline
    │
    ├─> Firecrawl (website content)
    ├─> ContactExtractor (emails, phones)
    ├─> SocialProfileExtractor (social links)
    └─> QualificationAgent (AI scoring)
    │
    ▼
Database (PostgreSQL)
    │
    │ Insert BusinessLead records
    │ Insert LeadContact records
    │ Insert LeadSocialProfile records
    │ Update DiscoveryJob status = COMPLETED
    ▼
Frontend (React Query)
    │
    │ Auto-refresh polling (10s interval)
    │ Display results in table
```

### 2. AI Agent Execution Flow

```
User Request
    │
    │ POST /api/v1/agents/execute
    │ { agent: "LeadQualificationAgent", lead_id: "uuid" }
    ▼
Agent Orchestrator
    │
    │ Load agent class
    │ Prepare context (lead data, ICP)
    ▼
AI Provider Router
    │
    ├─> Try Gemini 2.0 Flash (primary)
    │   │
    │   ├─> Success → Return structured output
    │   │
    │   └─> Failure → Fallback
    │
    ├─> Try OpenRouter (secondary)
    │   │
    │   ├─> Success → Return structured output
    │   │
    │   └─> Failure → Fallback
    │
    └─> Heuristic NLP (last resort)
        │
        └─> Rule-based analysis (never fails)
    │
    ▼
Validation & Storage
    │
    │ Validate against JSON schema
    │ Store AgentRun record
    │ Update lead qualification_score
    ▼
Return Results
```

### 3. Outreach Campaign Flow

```
Campaign Creation
    │
    │ POST /api/v1/campaigns
    │ { name, steps: [email, linkedin, call], audience_filter }
    ▼
Campaign Service
    │
    │ Create OutreachCampaign
    │ Create CampaignStep records
    ▼
Audience Selection
    │
    │ Query leads matching filters
    │ Apply suppression list
    │ Create CampaignMember records
    ▼
Approval Workflow
    │
    │ Generate draft messages (AI agent)
    │ Create OutreachApproval records
    │ Wait for manual review
    ▼
Execution (Celery)
    │
    ├─> Email channel (Gmail OAuth2)
    ├─> WhatsApp channel (Meta Business API)
    ├─> Social DM (Instagram, LinkedIn API)
    └─> SMS channel (provider integration)
    │
    ▼
Tracking & Analytics
    │
    │ Store ConversationMessage
    │ Track EmailEvent (sent, opened, clicked, replied)
    │ Update campaign metrics
```

### 4. RAG Knowledge Retrieval Flow

```
User Question
    │
    │ POST /api/v1/knowledge/search
    │ { query: "What is our pricing?", top_k: 5 }
    ▼
Knowledge Service
    │
    │ Generate embedding (Gemini text-embedding-004, 768-dim)
    ▼
pgvector Query
    │
    │ SELECT * FROM knowledge_chunks
    │ ORDER BY embedding <=> query_embedding
    │ LIMIT 5
    │ (Uses ivfflat index for fast similarity search)
    ▼
Context Assembly
    │
    │ Retrieve top K matching chunks
    │ Include source metadata
    ▼
LLM Generation
    │
    │ Prompt: "Answer based on context: {chunks}"
    │ Model: Gemini 2.0 Flash
    ▼
Response with Citations
    │
    │ { answer, sources: [doc_id, page, relevance_score] }
```

---

## Data Flow

### Request/Response Flow

```
1. Client Request
   └─> Browser/App sends HTTP request

2. CORS Check
   └─> Validate origin (production: exact match, dev: regex)

3. Security Headers
   └─> Add X-Frame-Options, CSP, HSTS, etc.

4. Request ID Assignment
   └─> Generate UUID, attach to request.state.request_id

5. Rate Limit Check
   └─> Query Redis for request count
   └─> If exceeded: return 429 Too Many Requests
   └─> Else: increment counter, proceed

6. Route Matching
   └─> FastAPI router matches path + method

7. Request Validation
   └─> Pydantic schema validates body/query/path params
   └─> If invalid: return 422 Unprocessable Entity

8. Dependency Injection
   └─> Inject database session, auth context, etc.

9. Business Logic Execution
   └─> Service layer methods
   └─> Provider calls (external APIs)
   └─> Database queries (SQLAlchemy)

10. Response Serialization
    └─> Pydantic models → JSON
    └─> Add X-Request-ID header

11. Metrics Collection
    └─> Prometheus records duration, status code

12. Error Tracking
    └─> If exception: send to Sentry
    └─> Return structured error response

13. Client Receives Response
    └─> React Query caches response (5min default)
```

### Data Persistence Flow

```
Application Data → SQLAlchemy ORM → PostgreSQL
                                       │
                                       ├─> Tables (17 models)
                                       ├─> Indexes (59 total)
                                       └─> pgvector embeddings

Cache Data → Redis
              │
              ├─> Rate limit counters (key: IP address)
              ├─> Celery task queue
              └─> Celery result backend

File Data → MinIO S3
             │
             ├─> Bucket: crm-assets
             ├─> Images (logos, profile pictures)
             ├─> Documents (PDFs, presentations)
             └─> Social media creatives
```

---

## Integration Points

### External API Integrations

**Lead Discovery Providers:**
- **Apify** (primary)
  - Endpoint: https://api.apify.com/v2/
  - Actor: Google Maps Scraper (nwua9Gu5YrADL7ZDj)
  - Timeout: 300s
  - Rate limit: Provider-managed
  
- **SerpAPI** (fallback)
  - Endpoint: https://serpapi.com/search
  - Type: Google Local Results
  - Timeout: 30s
  
- **Google Places API** (fallback)
  - Endpoint: https://maps.googleapis.com/maps/api/place/
  - Type: Text Search + Details
  - Timeout: 30s

**AI Service Providers:**
- **Google Gemini** (primary)
  - Model: gemini-2.0-flash-001
  - Embeddings: text-embedding-004 (768-dim)
  - Endpoint: https://generativelanguage.googleapis.com/
  
- **OpenRouter** (fallback)
  - Models: Claude 3.5 Sonnet, GPT-4o
  - Endpoint: https://openrouter.ai/api/v1/
  
- **Heuristic NLP** (last resort)
  - Local rule-based processing
  - Zero external dependency

**Communication Channels:**
- **Gmail API**
  - Auth: OAuth2
  - Scopes: gmail.send, gmail.readonly
  
- **WhatsApp Business API**
  - Provider: Meta
  - Endpoint: https://graph.facebook.com/v18.0/
  
- **Social Media APIs**
  - Instagram Graph API
  - Facebook Graph API
  - Twitter/X API v2
  - LinkedIn Marketing API

**Enrichment Services:**
- **Firecrawl**
  - Endpoint: https://api.firecrawl.dev/
  - Max pages: 5
  - Timeout: 60s

### Internal Service Communication

**Backend ↔ Database:**
- Protocol: PostgreSQL wire protocol (psycopg)
- Connection pool: 20 base + 10 overflow
- Health check: `pg_isready` every 10s

**Backend ↔ Redis:**
- Protocol: Redis protocol (redis-py)
- Use cases: Rate limiting, Celery queue, caching
- Health check: `redis-cli ping` every 10s

**Backend ↔ MinIO:**
- Protocol: S3 API (minio-py)
- Endpoint: http://minio:9000 (internal)
- Public URL: http://localhost:9000 (external)
- Health check: `/minio/health/live` every 15s

**Backend ↔ Celery Worker:**
- Message broker: Redis
- Result backend: Redis
- Serialization: JSON
- Task routing: Default queue

**Frontend ↔ Backend:**
- Protocol: HTTP/REST
- Base URL: http://localhost:8000/api/v1
- Auth: API key (future: JWT)
- Caching: React Query (5min staleTime)

---

## Technology Stack

### Frontend Stack

```
┌─────────────────────────────────────┐
│  Framework:    React 18              │
│  Language:     TypeScript 5.2        │
│  Build Tool:   Vite 5.1              │
│  Styling:      Tailwind CSS 3.4     │
│  Icons:        Lucide React          │
│  Routing:      React Router 6        │
│  Data Fetch:   TanStack Query 5      │
│  Forms:        Native + validation   │
│  Monitoring:   Sentry React SDK      │
└─────────────────────────────────────┘
```

### Backend Stack

```
┌─────────────────────────────────────┐
│  Framework:    FastAPI 0.109         │
│  Language:     Python 3.11+          │
│  Server:       Uvicorn 0.27          │
│  ORM:          SQLAlchemy 2.0        │
│  Migrations:   Alembic 1.13          │
│  Validation:   Pydantic 2.6          │
│  Tasks:        Celery 5.3            │
│  Rate Limit:   slowapi 0.1.9         │
│  Monitoring:   Sentry FastAPI SDK    │
│  Metrics:      Prometheus            │
└─────────────────────────────────────┘
```

### Data & Infrastructure Stack

```
┌─────────────────────────────────────┐
│  Database:     PostgreSQL 16         │
│  Vector:       pgvector 0.5.1        │
│  Cache:        Redis 7 Alpine        │
│  Storage:      MinIO (S3-compat)     │
│  Container:    Docker Compose        │
│  Networking:   Bridge network        │
└─────────────────────────────────────┘
```

### External Services

```
┌─────────────────────────────────────┐
│  Discovery:    Apify, SerpAPI        │
│  AI:           Gemini, OpenRouter    │
│  Enrichment:   Firecrawl             │
│  Email:        Gmail API             │
│  Messaging:    WhatsApp Meta API     │
│  Social:       IG, FB, X, LinkedIn   │
│  Monitoring:   Sentry                │
└─────────────────────────────────────┘
```

---

## Deployment Architecture

### Docker Compose Stack

```
┌─────────────────────────────────────────────────────────────┐
│                     Docker Network: crm-lead-network         │
│                            (Bridge Driver)                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────┐ │
│  │   PostgreSQL    │  │     Redis       │  │   MinIO    │ │
│  │   Container     │  │   Container     │  │ Container  │ │
│  │                 │  │                 │  │            │ │
│  │  Image: pgvect  │  │  Image: redis   │  │ Image:     │ │
│  │  Port: 5432     │  │  Port: 6379     │  │ minio      │ │
│  │  Memory: 1GB    │  │  Memory: 256MB  │  │ Ports:     │ │
│  │  Volume:        │  │  Volume:        │  │ 9000, 9001 │ │
│  │  postgres_data  │  │  redis_data     │  │ Memory:    │ │
│  │                 │  │                 │  │ 512MB      │ │
│  │  Health: ✅     │  │  Health: ✅     │  │ Volume:    │ │
│  │  pg_isready     │  │  redis ping     │  │ minio_data │ │
│  └─────────────────┘  └─────────────────┘  └────────────┘ │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Backend Container                        │  │
│  │                                                       │  │
│  │  Image: custom (./backend/Dockerfile)                │  │
│  │  Port: 8000                                          │  │
│  │  Memory: 512MB, CPU: 1.0                             │  │
│  │  Depends: postgres (healthy), redis (healthy),       │  │
│  │           minio (healthy)                            │  │
│  │  Command: alembic upgrade head && python main.py    │  │
│  │  Health: curl http://localhost:8000/api/v1/health   │  │
│  │  Restart: unless-stopped                             │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │            Celery Worker Container                    │  │
│  │                                                       │  │
│  │  Image: custom (./backend/Dockerfile)                │  │
│  │  Memory: 256MB                                       │  │
│  │  Depends: postgres, redis, backend, minio            │  │
│  │  Command: celery -A app.workers.celery_app worker   │  │
│  │           --loglevel=info --concurrency=2            │  │
│  │  Restart: unless-stopped                             │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │             Frontend Container                        │  │
│  │                                                       │  │
│  │  Image: custom (./frontend/Dockerfile)               │  │
│  │  Port: 3000                                          │  │
│  │  Memory: 256MB                                       │  │
│  │  Depends: backend (healthy)                          │  │
│  │  Health: wget http://localhost:3000/                 │  │
│  │  Restart: unless-stopped                             │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘

External Access:
  - Frontend:   http://localhost:3000
  - Backend:    http://localhost:8000
  - API Docs:   http://localhost:8000/docs
  - PostgreSQL: localhost:5432 (admin access)
  - Redis:      localhost:6379 (admin access)
  - MinIO UI:   http://localhost:9001
```

### Resource Allocation

| Service | Memory Limit | Memory Reserved | CPU Limit | Notes |
|---------|--------------|-----------------|-----------|-------|
| PostgreSQL | 1GB | 512MB | - | Database needs more memory |
| Redis | 256MB | 128MB | - | Lightweight cache |
| MinIO | 512MB | 256MB | - | Object storage |
| Backend | 512MB | 256MB | 1.0 | API server |
| Celery | 256MB | 128MB | - | Background worker |
| Frontend | 256MB | 128MB | - | Static assets |
| **Total** | **2.75GB** | **1.4GB** | **1.0 CPU** | - |

### Network Configuration

- **Network Name:** crm-lead-network
- **Driver:** bridge
- **Port Bindings:** All external ports bound to 127.0.0.1 (localhost only) for security
- **Service Discovery:** Containers reference each other by service name (e.g., `postgres:5432`)

### Volume Management

- **postgres_data:** Persistent PostgreSQL data directory
- **redis_data:** Persistent Redis AOF logs
- **minio_data:** Persistent object storage
- **Backup Strategy:** Not yet implemented (see recommendations)

---

## Security Architecture

### Defense in Depth

```
Layer 1: Network Security
  ├─> Localhost-only port bindings (127.0.0.1)
  ├─> Docker bridge network isolation
  └─> No public container exposure

Layer 2: Application Security
  ├─> CORS (conditional: strict in production)
  ├─> Rate limiting (Redis-backed, per-IP)
  ├─> Input validation (Pydantic schemas)
  └─> SSRF protection (private IP blocking)

Layer 3: Transport Security
  ├─> Security headers (HSTS, CSP, X-Frame-Options, etc.)
  ├─> TLS/SSL (to be configured in production)
  └─> Secure cookie flags

Layer 4: Data Security
  ├─> Environment variable secrets
  ├─> No hardcoded credentials
  ├─> SQL injection prevention (ORM parameterization)
  └─> XSS prevention (React JSX escaping)

Layer 5: Monitoring & Audit
  ├─> Request tracing (X-Request-ID)
  ├─> Error tracking (Sentry)
  ├─> Metrics collection (Prometheus)
  └─> Structured logging (JSON format)
```

---

## Scalability Considerations

### Current Capacity

- **Concurrent Users:** ~100-200 (single backend instance)
- **Database Connections:** 30 max (20 + 10 overflow)
- **Celery Workers:** 2 concurrent tasks
- **Redis:** Single instance (no replication)

### Horizontal Scaling Path

```
Load Balancer (Nginx/HAProxy)
    │
    ├─> Backend Instance 1 ─┐
    ├─> Backend Instance 2 ─┼─> PostgreSQL (Primary)
    ├─> Backend Instance 3 ─┘      │
    │                              └─> Read Replicas
    │
    ├─> Celery Worker Pool (Auto-scaling)
    │
    └─> Redis Cluster (Sentinel/Cluster mode)

Object Storage: MinIO distributed mode or S3
```

### Performance Optimizations

1. **Database:**
   - 59 indexes for query optimization
   - Connection pooling (20 base + 10 overflow)
   - pgvector ivfflat index for semantic search

2. **API:**
   - Redis-backed rate limiting (minimal latency)
   - Prometheus metrics (low overhead)

3. **Frontend:**
   - Code splitting (route-based lazy loading)
   - React Query caching (5min staleTime)
   - Smart polling (only when needed)

4. **Background Jobs:**
   - Celery task queue (async execution)
   - Concurrent worker support (2 base, expandable)

---

## Conclusion

The CRM Lead Discovery platform follows modern architectural patterns with:

- ✅ **Clean separation of concerns** across layers
- ✅ **Scalable microservices-inspired design** within a monolith
- ✅ **Production-ready infrastructure** with Docker orchestration
- ✅ **Comprehensive security** with defense in depth
- ✅ **Observable systems** with monitoring and tracing
- ✅ **Performance optimized** with indexes and caching

The architecture supports the current scale and provides clear paths for horizontal scaling as the system grows.

---

**Document Version:** 1.0  
**Last Updated:** November 10, 2026  
**Maintained By:** Engineering Team
