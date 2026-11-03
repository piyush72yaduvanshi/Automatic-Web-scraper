# Updated Environment Variables Reference Manual

**System**: AI Sales, Lead Generation, Outreach & Marketing Operating System  
**Version**: 2.0.0  
**Updated**: November 3, 2026  

---

## 1. Overview & Configuration Strategy

The application is configured using environment variables loaded from a root `.env` file via `pydantic-settings`. 

### Graceful Fallback Design
The system is built to be resilient in development, testing, and production:
- **No API keys?** The system runs smoothly in offline mode using `HeuristicAIProvider` and simulated third-party responses.
- **No PostgreSQL?** The SQLAlchemy layer runs seamlessly against SQLite (`test.db` / `crm_leads.db`).
- **No Redis?** The native workflow engine executes synchronously or via in-memory event queues.

---

## 2. Environment Variables Catalog

### 2.1. Infrastructure & Databases

| Variable Name | Required? | Default Value | Description |
|:---|:---:|:---|:---|
| `DATABASE_URL` | Optional | `sqlite+aiosqlite:///./crm_leads.db` | Primary database connection string. In production, use `postgresql+asyncpg://postgres:postgres@localhost:5432/crm_sales_os`. |
| `REDIS_URL` | Optional | `redis://localhost:6379/0` | Redis instance for Celery task queuing and distributed rate-limiting. |
| `CELERY_BROKER_URL` | Optional | `redis://localhost:6379/0` | Celery message broker endpoint. |
| `CELERY_RESULT_BACKEND`| Optional | `redis://localhost:6379/1` | Celery task result storage endpoint. |

### 2.2. AI Providers & Routing

| Variable Name | Required? | Default Value | Description |
|:---|:---:|:---|:---|
| `GEMINI_API_KEY` | Optional | `""` (Empty string) | Google Gemini API key for Gemini 1.5 Pro and Flash models. |
| `OPENROUTER_API_KEY` | Optional | `""` (Empty string) | OpenRouter API key for Claude 3.5 Sonnet, GPT-4o, and Llama 3 models. |
| `PRIMARY_AI_PROVIDER`| Optional | `gemini` | Preferred AI provider: `gemini`, `openrouter`, or `heuristic`. |

### 2.3. Email Deliverability & Outbound Safeguards (Phase 2)

| Variable Name | Required? | Default Value | Description |
|:---|:---:|:---|:---|
| `OUTBOUND_KILL_SWITCH` | Optional | `false` | Master circuit breaker. If `true`, all outbound messaging is immediately blocked. |
| `MAX_DAILY_SENDS_PER_INBOX` | Optional | `50` | Maximum email send quota permitted per mailbox per 24-hour cycle. |
| `BOUNCE_RATE_THRESHOLD` | Optional | `5.0` | Maximum allowable bounce rate percentage before automated campaign pause. |
| `COMPLAINT_RATE_THRESHOLD` | Optional | `0.1` | Maximum allowable spam complaint rate percentage before mailbox freeze. |
| `PREVENT_DUPLICATE_SENDS` | Optional | `true` | Enforces 24-hour SHA-256 fingerprint deduplication check. |

### 2.4. Inbound & Outbound Messaging Providers

| Variable Name | Required? | Default Value | Description |
|:---|:---:|:---|:---|
| `SMTP_HOST` | Optional | `""` | Outbound SMTP host (e.g. `smtp.gmail.com`). |
| `SMTP_PORT` | Optional | `587` | SMTP port (587 for TLS, 465 for SSL). |
| `SMTP_USER` | Optional | `""` | SMTP sender username / mailbox. |
| `SMTP_PASSWORD` | Optional | `""` | SMTP sender application password. |
| `GMAIL_CLIENT_ID` | Optional | `""` | Google Workspace OAuth 2.0 Client ID for Gmail API. |
| `GMAIL_CLIENT_SECRET` | Optional | `""` | Google Workspace OAuth 2.0 Client Secret. |
| `WHATSAPP_API_TOKEN` | Optional | `""` | Meta WhatsApp Cloud API access token. |
| `WHATSAPP_PHONE_NUMBER_ID` | Optional | `""` | Meta WhatsApp sender phone number ID. |

### 2.5. Social Media & Content Publishing (Phase 2)

| Variable Name | Required? | Default Value | Description |
|:---|:---:|:---|:---|
| `LINKEDIN_CLIENT_ID` | Optional | `""` | LinkedIn Developer OAuth Client ID. |
| `LINKEDIN_CLIENT_SECRET`| Optional| `""` | LinkedIn Developer OAuth Client Secret. |
| `TWITTER_API_KEY` | Optional | `""` | X / Twitter Developer API Key. |
| `TWITTER_API_SECRET` | Optional | `""` | X / Twitter Developer API Secret. |
| `REDDIT_CLIENT_ID` | Optional | `""` | Reddit App Script Client ID. |
| `REDDIT_CLIENT_SECRET` | Optional| `""` | Reddit App Script Secret. |

> [!NOTE]
> When social API credentials are left blank, the `ContentMarketingService` operates safely in **Simulation Mode**, marking scheduled calendar entries as `NOT_CONFIGURED` to prevent runtime crashes or false delivery claims.

### 2.6. Lead Discovery & Scrapers

| Variable Name | Required? | Default Value | Description |
|:---|:---:|:---|:---|
| `SERPAPI_API_KEY` | Optional | `""` | SerpAPI key for Google Search and Google Maps business queries. |
| `APIFY_API_TOKEN` | Optional | `""` | Apify API token for Google Maps Scraper actors. |
| `FIRECRAWL_API_KEY` | Optional | `""` | Firecrawl API key for clean markdown web scraping. |

---

## 3. Sample `.env` Template

```ini
# ==============================================================================
# AI SALES & CRM OPERATING SYSTEM — ENVIRONMENT CONFIGURATION
# ==============================================================================

# Application Environment
ENVIRONMENT=development
LOG_LEVEL=INFO

# Database & Cache (PostgreSQL 16 & Redis 7 in Docker)
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/crm_sales_os
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# AI Providers (At least one recommended for live AI responses)
GEMINI_API_KEY=your_gemini_api_key_here
OPENROUTER_API_KEY=your_openrouter_api_key_here
PRIMARY_AI_PROVIDER=gemini

# Phase 2 Deliverability Safeguards
OUTBOUND_KILL_SWITCH=false
MAX_DAILY_SENDS_PER_INBOX=50
BOUNCE_RATE_THRESHOLD=5.0
COMPLAINT_RATE_THRESHOLD=0.1
PREVENT_DUPLICATE_SENDS=true

# Lead Generation APIs (Optional)
SERPAPI_API_KEY=
APIFY_API_TOKEN=
FIRECRAWL_API_KEY=

# Email SMTP / Gmail (Optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=

# WhatsApp Cloud API (Optional)
WHATSAPP_API_TOKEN=
WHATSAPP_PHONE_NUMBER_ID=

# Social Media OAuth (Optional - defaults to NOT_CONFIGURED simulation)
LINKEDIN_CLIENT_ID=
TWITTER_API_KEY=
REDDIT_CLIENT_ID=
```

