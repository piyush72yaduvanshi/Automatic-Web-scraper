# AI Sales, CRM, Outreach & Marketing Operating System

An enterprise-grade, autonomous, fault-tolerant operating system pairing high-throughput multi-source lead discovery with a relational CRM, 15 specialized AI reasoning agents, native Python workflow automation (Zero n8n), multi-platform social media publishing, MinIO object storage, and pgvector semantic retrieval.

---

## 🌟 Key Capabilities & Modules

### 1. Lead Discovery & Multi-Scanner
- **Multi-Source Scraping**: Google Places API, Google Maps via SerpAPI & Apify, and Firecrawl deep-web crawlers.
- **Entity Extraction**: Robust contact extractors for verified emails, normalized E.164 phone numbers, and social media handles.
- **Deduplication & Provenance**: Evidence tracking with SHA-256 fingerprinting and source confidence scoring.

### 2. Relational CRM & Pipeline
- **Entity Graph**: Complete relational models for Companies, Contacts, Deals, Pipelines, Stages, Activities, Tasks, and Meetings.
- **Deals Kanban**: Interactive drag-and-drop sales pipeline with stage velocity, deal values, and 1-click lead conversion.
- **Company Dossiers**: Strict three-way truth separation: `verified_facts`, `inferred_insights`, and `unknowns` (zero AI hallucinations).

### 3. AI Intelligence & 15 Specialized Agents
- **Multi-Model Orchestration**: Priority routing via Google Gemini 2.0 Flash / Pro with failover to OpenRouter (Claude 3.5 Sonnet, GPT-4o) and zero-crash offline Heuristic NLP.
- **Specialized Agents**: 15 scoped agents covering lead research, ICP qualification (5-factor weighted scoring), email copywriting, reply sentiment analysis, meeting prep, and deal closing.
- **Knowledge Base RAG**: Semantic text chunking with native PostgreSQL `pgvector` 768-dimensional embeddings and cosine similarity ranking.

### 4. Zero n8n Native Workflow Automation
- **Event-Driven Architecture**: 100% native Python event bus with 11 domain event triggers, conditional branch evaluation, retry policies, and execution audit logging.
- **Deliverability & Safety**: Live DNS record verification (SPF, DKIM, DMARC, MX via `dnspython`), daily send quotas, bounce/complaint circuit breakers, and an instant Global Outbound Kill Switch.
- **Human-in-the-Loop Outreach**: Mandatory approval queue gatekeeper for all outbound emails and WhatsApp messages.

### 5. Multi-Platform Social Media Studio
- **Official API Integrations**: Instagram (Meta Graph API), Facebook Pages API, X (Twitter) Developer API v2, and LinkedIn Marketing API (Personal Profile & Company Page).
- **AI Social Studio**: Automated multi-format post generation, hook research, hashtag analysis, carousel briefs, and interactive live previews.
- **Object Storage**: MinIO S3-compatible asset store with automatic local disk fallback for creatives and media uploads.

---

## 🛠️ Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Backend** | Python 3.11+, FastAPI, SQLAlchemy 2.0, Pydantic v2, Alembic, Celery, httpx, dnspython |
| **Databases & Cache** | PostgreSQL 16 with native `pgvector`, Redis 7, MinIO S3 Object Storage |
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS, Lucide Icons, TanStack Query |
| **DevOps & Containers** | Docker, Docker Compose, Nginx, Healthcheck probes |

---

## 🚀 Quick Start Guide

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Node.js 18+ and npm

### 1. Start Infrastructure Services
```bash
docker compose up -d
```
This spins up:
- PostgreSQL 16 on `localhost:5432` (with pgvector extension)
- Redis 7 on `localhost:6379`
- MinIO Object Storage on `localhost:9000` (Console on `localhost:9001`)

### 2. Backend Setup
```bash
cd backend
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
cp ../.env.example .env
python main.py
```
FastAPI backend will run on **http://localhost:8000** with interactive Swagger documentation at **http://localhost:8000/docs**.

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Vite React frontend will run on **http://localhost:5173**.

---

## 🧪 Testing

Run the full automated test suite (60 tests across API, CRM, AI, Deliverability, Workflows, MinIO, and Social):
```bash
cd backend
pytest tests/ -v
```

---

## 📚 Technical Documentation

Detailed engineering specifications and architecture guides are organized in [`docs/`](./docs/):

- 🏛️ [System Architecture](./docs/ARCHITECTURE.md)
- 🗄️ [Database Schema & Entity Models](./docs/DATABASE_SCHEMA.md)
- 🔌 [API Endpoints Reference](./docs/API_DOCUMENTATION.md)
- ⚙️ [Environment Variables Guide](./docs/ENVIRONMENT_VARIABLES.md)
- 🤖 [15 Specialized AI Agents](./docs/AGENT_DOCUMENTATION.md)
- ⚡ [Native Workflow Automation Engine](./docs/WORKFLOW_ENGINE_DOCUMENTATION.md)
- 📱 [Social Media Automation Engine](./docs/SOCIAL_MEDIA_AUTOMATION.md)
- 📬 [Email Deliverability & Mailbox Health](./docs/EMAIL_DELIVERABILITY.md)
- 🛡️ [Security Review & SSRF Controls](./docs/SECURITY_REVIEW.md)
- 🐳 [Docker Setup & Deployment Guide](./docs/DOCKER_SETUP.md)

---

## 📄 License
Proprietary & Confidential. All rights reserved.
