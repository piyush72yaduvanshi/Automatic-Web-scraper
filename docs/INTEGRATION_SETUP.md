# AI Sales & CRM Operating System — Integration Setup Guide

## 1. Overview

The AI Sales & CRM Operating System interfaces with best-in-class AI models, business discovery scrapers, and communication channels. 

> [!IMPORTANT]
> **Zero-Crash Architecture**: Every external integration is completely optional for initial system boot. If an API key or token is omitted, the system automatically falls back to safe development simulation mode (for Gmail and WhatsApp) or offline deterministic NLP heuristics (for AI agents), keeping all 15 user interface views, CRM features, and qualification algorithms fully operational.

---

## 2. AI Intelligence Providers

### 2.1. Google Gemini API (Primary AI Engine)
Google Gemini 1.5/2.0 Flash is the primary reasoning engine for lead scoring, company intelligence dossiers, and personalized outreach drafts.

1. Navigate to [Google AI Studio](https://aistudio.google.com/).
2. Click **Get API key** and create a key in a new or existing Google Cloud project.
3. Add the key to your `.env` file:
   ```env
   GEMINI_API_KEY=AIzaSy...your_gemini_api_key...
   ```
4. Verify connectivity:
   - Navigate to the **Integrations** tab in the web dashboard (`/integrations`).
   - Locate the **Gemini** card and click **Validate Connection**.
   - If valid, the status will switch to `HEALTHY`.

---

### 2.2. OpenRouter (Secondary / Failover AI Engine)
OpenRouter provides automated multi-model redundancy (Claude 3.5 Sonnet, Llama 3 70B, GPT-4o) if Gemini encounters rate limits or service interruptions.

1. Navigate to [OpenRouter](https://openrouter.ai/).
2. Create an account, go to **Keys**, and click **Create Key**.
3. Add to your `.env` file:
   ```env
   OPENROUTER_API_KEY=sk-or-v1-...your_openrouter_key...
   ```
4. The system will automatically fail over to OpenRouter if Gemini returns an HTTP 429 or 5xx error.

---

## 3. Lead Discovery Scrapers

### 3.1. SerpAPI (Google Maps Business Discovery)
SerpAPI handles structured Google Maps and local pack searches with geo-coordinate targeting and review extraction.

1. Sign up at [SerpAPI](https://serpapi.com/).
2. Copy your API Key from the dashboard.
3. Add to `.env`:
   ```env
   SERPAPI_API_KEY=your_serpapi_key_here
   ```

---

### 3.2. Apify (Actor Scrapers)
Apify provides high-volume Google Maps and business directory scraping actors.

1. Create an account at [Apify](https://apify.com/).
2. Go to **Settings -> Integrations** and copy your **Personal API Token**.
3. Add to `.env`:
   ```env
   APIFY_API_KEY=apify_api_...your_token...
   ```

---

### 3.3. Firecrawl (Web & Markdown Scraping)
Firecrawl turns company website URLs into clean, LLM-ready markdown for deep intelligence analysis.

1. Sign up at [Firecrawl.dev](https://www.firecrawl.dev/).
2. Obtain your API Key from the dashboard.
3. Add to `.env`:
   ```env
   FIRECRAWL_API_KEY=fc-...your_firecrawl_key...
   ```

---

## 4. Communication & Messaging Channels

### 4.1. Gmail API via Google Workspace OAuth 2.0
The Gmail integration handles authorized email synchronization, thread management, and Human-Approved outbound email sending.

#### Step 1: Create Google Cloud Project & Enable Gmail API
1. Open the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project named `AI-Sales-CRM-OS`.
3. Go to **APIs & Services -> Library**, search for **Gmail API**, and click **Enable**.

#### Step 2: Configure OAuth Consent Screen
1. Go to **APIs & Services -> OAuth consent screen**.
2. Select **External** (or **Internal** if using Google Workspace).
3. Fill in App Name (`AI Sales OS`) and User Support Email.
4. Add Scopes:
   - `https://www.googleapis.com/auth/gmail.send`
   - `https://www.googleapis.com/auth/gmail.readonly`
   - `https://www.googleapis.com/auth/gmail.modify`
5. Under **Test users**, add your personal Google account email address.

#### Step 3: Create OAuth 2.0 Client Credentials
1. Go to **APIs & Services -> Credentials -> Create Credentials -> OAuth client ID**.
2. Select Application type: **Web application**.
3. Under **Authorized redirect URIs**, add:
   ```text
   http://localhost:8000/api/v1/outreach/gmail/oauth/callback
   ```
4. Copy the generated **Client ID** and **Client Secret** into your `.env`:
   ```env
   GMAIL_CLIENT_ID=xxxx.apps.googleusercontent.com
   GMAIL_CLIENT_SECRET=GOCSPX-xxxx
   GMAIL_REDIRECT_URI=http://localhost:8000/api/v1/outreach/gmail/oauth/callback
   ```

#### Step 4: Refresh Token Generation
When you first authenticate via the Settings view, your Google account yields a persistent refresh token stored in `GMAIL_REFRESH_TOKEN`.
*(If credentials are omitted, `GmailProvider` operates in safe simulation mode, logging outbound dispatches without failing).*

---

### 4.2. Meta WhatsApp Business Cloud API
Enables direct messaging, inbound customer conversations, and automated opt-out processing.

#### Step 1: Create Meta Developer App
1. Go to [Meta for Developers](https://developers.facebook.com/) and create a Business App.
2. Add the **WhatsApp** product to your app.

#### Step 2: Retrieve Phone Number ID and System User Token
1. In the WhatsApp API Setup panel, copy your **Phone Number ID**.
2. Create a **System User** in Meta Business Manager with permissions to `whatsapp_business_messaging`.
3. Generate a permanent System User Access Token.
4. Update your `.env`:
   ```env
   WHATSAPP_API_TOKEN=EAAG...your_system_user_token...
   WHATSAPP_PHONE_NUMBER_ID=109283746501928
   WHATSAPP_VERIFY_TOKEN=your_secure_random_webhook_token_here
   ```

#### Step 3: Configure Inbound Webhook
1. In the Meta App Dashboard, navigate to **WhatsApp -> Configuration -> Webhook**.
2. Callback URL: `https://your-public-domain.com/api/v1/outreach/whatsapp/webhook`
3. Verify Token: Match the value entered in `WHATSAPP_VERIFY_TOKEN`.
4. Subscribe to the `messages` webhook field.
5. Inbound opt-outs (e.g. prospect replies "STOP") are automatically registered in `suppression_records`.

---

## 5. Storage & Background Infrastructure

### 5.1. PostgreSQL 16
Production relational database storage.
```env
DATABASE_URL=postgresql://crm_user:crm_password@localhost:5432/crm_db
```
*(If unreachable or left unset, the system automatically falls back to local SQLite at `crm_leads.db`)*.

### 5.2. Redis & Celery
Asynchronous task execution broker and caching layer.
```env
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```
To run the Celery background worker:
```bash
cd backend
celery -A app.core.celery_app worker --loglevel=info -P solo
```
*(Note: On Windows machines, the `-P solo` pool flag prevents multiprocessing semaphore deadlocks).*

