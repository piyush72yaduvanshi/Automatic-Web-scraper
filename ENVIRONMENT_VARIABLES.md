# AI Sales & CRM Operating System — Environment Variables Reference

## 1. Overview

This document catalogs every environment variable supported by the AI Sales & CRM Operating System. 

The configuration layer (`backend/app/core/config.py`) uses **Pydantic Settings** to validate variables upon startup. All variables have sensible defaults enabling the entire application to start and operate in local development or test mode without third-party API dependencies.

---

## 2. Environment Variables Catalog

### 2.1. Core Application & Server

| Variable Name | Required? | Default Value | Description & Operational Impact if Omitted |
| :--- | :--- | :--- | :--- |
| `APP_NAME` | Optional | `AI Sales & CRM Operating System` | Descriptive system name shown in logs and UI. |
| `APP_ENV` | Optional | `development` | Environment mode (`development`, `staging`, `production`). In development, verbose debug endpoints are active. |
| `DEBUG` | Optional | `true` | Enables FastAPI auto-reload and detailed traceback generation. |
| `API_V1_PREFIX` | Optional | `/api/v1` | URL path prefix for all version 1 REST API routes. |
| `BACKEND_HOST` | Optional | `0.0.0.0` | Network interface IP binding for the Uvicorn ASGI server. |
| `BACKEND_PORT` | Optional | `8000` | Port listening for incoming HTTP connections. |
| `FRONTEND_URL` | Optional | `http://localhost:5173` | Allowed frontend client URL for CORS headers. |

---

### 2.2. Persistence & Asynchronous Infrastructure

| Variable Name | Required? | Default Value | Description & Operational Impact if Omitted |
| :--- | :--- | :--- | :--- |
| `DATABASE_URL` | Optional | `postgresql+psycopg://postgres:postgres@localhost:5432/crm_leads` | Connection string for PostgreSQL 16. **Impact if omitted or unreachable**: The engine traps the error and automatically creates a local SQLite database at `crm_leads.db`. |
| `DATABASE_POOL_SIZE`| Optional | `20` | Number of persistent pooled connections maintained in PostgreSQL. Ignored on SQLite. |
| `DATABASE_MAX_OVERFLOW`| Optional | `10` | Maximum surge connections permitted above `DATABASE_POOL_SIZE`. |
| `REDIS_URL` | Optional | `redis://localhost:6379/0` | Redis caching and broker endpoint. **Impact if omitted**: Long tasks run synchronously in-process. |
| `CELERY_BROKER_URL` | Optional | `redis://localhost:6379/0` | Celery message queue connection string. |
| `CELERY_RESULT_BACKEND`| Optional | `redis://localhost:6379/0` | Celery task state and result storage. |

---

### 2.3. AI Intelligence & LLM Providers

| Variable Name | Required? | Default Value | Description & Operational Impact if Omitted |
| :--- | :--- | :--- | :--- |
| `DEFAULT_AI_PROVIDER`| Optional | `gemini` | Primary AI provider name (`gemini`, `openrouter`, `heuristic`). |
| `GEMINI_API_KEY` | Optional | `""` | Google Gemini API Key. **Impact if omitted**: Gemini provider is marked `NOT_CONFIGURED` in health service. Requests automatically fail over to OpenRouter, or `HeuristicAIProvider` (0-crash deterministic scoring). |
| `OPENROUTER_API_KEY`| Optional | `""` | OpenRouter API Key for multi-model failover. **Impact if omitted**: Secondary fallback bypassed. |
| `OPENROUTER_MODEL` | Optional | `google/gemini-2.0-flash-001` | LLM model checkpoint requested from OpenRouter. |

---

### 2.4. Lead Discovery & Scrapers

| Variable Name | Required? | Default Value | Description & Operational Impact if Omitted |
| :--- | :--- | :--- | :--- |
| `SERPAPI_API_KEY` | Optional | `""` | SerpAPI Key for Google Maps & search results. **Impact if omitted**: Maps scraper uses direct HTTP fallback or Apify. |
| `APIFY_API_TOKEN` | Optional | `""` | Apify Token for actor scraping pipelines. |
| `APIFY_MAPS_ACTOR_ID`| Optional | `nwua9Gu5YrADL7ZDj` | Actor ID for high-volume Google Maps crawls. |
| `FIRECRAWL_API_KEY`| Optional | `""` | Firecrawl Key for deep webpage-to-markdown conversion. **Impact if omitted**: Built-in BeautifulSoup extractor parses target HTML. |
| `FIRECRAWL_MAX_PAGES`| Optional | `5` | Maximum pages crawled per prospect domain. |

---

### 2.5. Communication Channels (Email & WhatsApp)

| Variable Name | Required? | Default Value | Description & Operational Impact if Omitted |
| :--- | :--- | :--- | :--- |
| `GMAIL_CLIENT_ID` | Optional | `""` | Google Cloud OAuth 2.0 Web Application Client ID. **Impact if omitted**: `GmailProvider` operates in safe simulation mode. |
| `GMAIL_CLIENT_SECRET`| Optional | `""` | Google Cloud OAuth 2.0 Client Secret. |
| `GMAIL_REFRESH_TOKEN`| Optional | `""` | Persistent OAuth 2.0 refresh token for sending. |
| `GMAIL_REDIRECT_URI` | Optional | `http://localhost:8000/api/v1/integrations/gmail/callback` | OAuth redirect URI callback. |
| `GMAIL_SENDER_EMAIL`| Optional | `""` | Authorized sender email address. |
| `WHATSAPP_PHONE_NUMBER_ID` | Optional | `""` | Meta WhatsApp Cloud API Phone Number ID. **Impact if omitted**: `WhatsAppProvider` operates in safe simulation mode. |
| `WHATSAPP_ACCESS_TOKEN` | Optional | `""` | Meta Permanent System User Access Token. |
| `WHATSAPP_VERIFY_TOKEN` | Optional | `crm_whatsapp_verify_token_default` | Secret token verifying Meta webhook subscription. |

---

### 2.6. AI Qualification Factor Weights (Sum = 1.0)

| Variable Name | Required? | Default Value | Description & Operational Impact if Omitted |
| :--- | :--- | :--- | :--- |
| `ICP_WEIGHT_FIT` | Optional | `0.25` | Weight for Ideal Customer Profile industry & size alignment (25%). |
| `ICP_WEIGHT_PAIN` | Optional | `0.25` | Weight for identified business problems & operational friction (25%). |
| `ICP_WEIGHT_TIMING` | Optional | `0.20` | Weight for timing indicators, expansions, and intent signals (20%). |
| `ICP_WEIGHT_REACHABILITY`| Optional | `0.15` | Weight for direct decision-maker contact availability (15%). |
| `ICP_WEIGHT_EVIDENCE` | Optional | `0.15` | Weight for multi-source confirmation and review presence (15%). |

---

### 2.7. Security, Access & Crawl Safeguards

| Variable Name | Required? | Default Value | Description & Operational Impact if Omitted |
| :--- | :--- | :--- | :--- |
| `SECRET_KEY` | Optional | `change-this-production-secret-key-32-chars-min` | Cryptographic secret for signing tokens and sessions. Must be changed in production. |
| `ADMIN_API_KEY` | Optional | `dev-admin-key-ai-sales-crm` | Master API key required in `X-API-Key` or `Authorization: Bearer` headers when `AUTH_ENABLED=true`. |
| `AUTH_ENABLED` | Optional | `false` | Global API authentication switch. Set to `true` in production to enforce API key checks on all routes. |
| `ALLOWED_ORIGINS` | Optional | `http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000` | Comma-delimited list of authorized origins for CORS pre-flight responses. |
| `ALLOW_PRIVATE_IPS` | Optional | `false` | SSRF protection switch. When `false`, outbound scrapers reject IP ranges: `127.0.0.0/8`, `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `169.254.169.254`. |
| `BLOCKED_DOMAINS` | Optional | `localhost,127.0.0.1,0.0.0.0` | Comma-delimited list of blocked hostname destinations. |
| `RATE_LIMIT_PER_MINUTE`| Optional | `60` | Client request rate throttle limit. |
| `RATE_LIMIT_BURST` | Optional | `10` | Temporary surge burst capacity above rate limit. |

