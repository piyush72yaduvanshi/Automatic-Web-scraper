# API Keys & Credentials Request Document

**Project**: AI Sales, Lead Generation, Outreach & Social Media Operating System  
**Prepared For**: Team Lead (TL) / Engineering Management / DevOps  
**Date**: November 2026  
**Document Purpose**: Consolidated access and credential request for live third-party APIs across AI, Lead Discovery, Email Infrastructure, WhatsApp, and Multi-Platform Social Media Automation.

---

## Ready-to-Send Message for Team Lead (TL)

> **Subject**: Access & API Credentials Request for AI Sales & CRM Operating System
>
> Hi **[TL Name]**,
>
> We have completed the implementation and testing of our **AI Sales, CRM, Outreach & Social Media Operating System** (all 54 backend automated tests passing, frontend production build verified).
>
> Currently, the system runs safely in offline/simulation mode. To enable **live data scraping, AI intelligence, automated email outreach, WhatsApp, and social media posting**, we need the API keys and credentials listed in the document below.
>
> I have grouped them by **Priority Level** along with the exact portal URLs, required permission scopes, and purpose for each key.
>
> Could you please review and provision or share these keys so we can update our production environment?
>
> Thank you!  
> **[Your Name]**

---

## Summary Matrix of Required Keys

| # | Environment Variable | Service / Provider | Priority | Purpose |
|:---:|:---|:---|:---:|:---|
| 1 | `GEMINI_API_KEY` | Google AI Studio / Vertex AI | **P1 (Critical)** | Core AI reasoning, research, ICP qualification, cold email copywriting |
| 2 | `OPENROUTER_API_KEY` | OpenRouter | **P1 (Critical)** | Secondary failover AI provider (Claude 3.5 Sonnet, GPT-4o) |
| 3 | `SERPAPI_API_KEY` | SerpAPI | **P1 (Critical)** | Google Maps business discovery & Google search lead extraction |
| 4 | `FIRECRAWL_API_KEY` | Firecrawl | **P1 (Critical)** | Clean web scraping of company websites to extract tech stacks & emails |
| 5 | `APIFY_API_TOKEN` | Apify | **P2 (High)** | High-volume Google Maps Scraper actor for bulk lead discovery |
| 6 | `SMTP_USER` & `SMTP_PASSWORD` *(or Gmail OAuth)* | Google Workspace / SMTP | **P1 (Critical)** | Live cold email outreach & transactional sequence dispatch |
| 7 | `GMAIL_CLIENT_ID` & `GMAIL_CLIENT_SECRET` | Google Cloud Console | **P2 (High)** | Two-way Gmail inbox sync & unified thread monitoring |
| 8 | `WHATSAPP_ACCESS_TOKEN` & `PHONE_NUMBER_ID` | Meta WhatsApp Cloud API | **P2 (High)** | Omnichannel WhatsApp business messaging & reply ingestion |
| 9 | `LINKEDIN_ACCESS_TOKEN` & URNs | LinkedIn Developer Portal | **P2 (High)** | Automated posting to LinkedIn Personal Profile & Company Page |
| 10 | `TWITTER_API_KEY`, `ACCESS_TOKEN` & `BEARER_TOKEN` | X (Twitter) Developer Portal | **P2 (High)** | Automated tweet & thread publishing via X API v2 |
| 11 | `INSTAGRAM_ACCESS_TOKEN` & `BUSINESS_ACCOUNT_ID` | Meta Graph API | **P3 (Medium)** | Instagram feed post & visual creative publishing |
| 12 | `FACEBOOK_PAGE_ACCESS_TOKEN` & `PAGE_ID` | Meta Graph API | **P3 (Medium)** | Facebook Corporate Page feed publishing |

---

## Detailed Credential Breakdown & Acquisition Guides

---

### GROUP 1: AI Intelligence Providers (P1 — Critical)

#### 1. Google Gemini API
- **Variable Name**: `GEMINI_API_KEY`
- **Where to get it**: [Google AI Studio](https://aistudio.google.com/app/apikey) or Google Cloud Console (Vertex AI).
- **Required Permission**: Standard API Access to `gemini-1.5-pro` and `gemini-1.5-flash`.
- **Purpose**: Powering the 15 specialized AI agents (Lead Research, ICP Scoring, Email Copywriting, Social Repurposing, Meeting Dossiers).
- **Cost / Free Tier**: Generous free tier (up to 15 RPM free on AI Studio); pay-as-you-go thereafter.

#### 2. OpenRouter API (Failover Provider)
- **Variable Name**: `OPENROUTER_API_KEY`
- **Where to get it**: [OpenRouter Dashboard](https://openrouter.ai/keys)
- **Required Permission**: Account API Key with access to `anthropic/claude-3.5-sonnet` and `openai/gpt-4o`.
- **Purpose**: Automatic zero-crash failover when primary AI provider experiences rate-limiting or latency spikes.
- **Cost**: Pay-as-you-go credit balance ($5–$10 deposit is sufficient for thousands of calls).

---

### GROUP 2: Lead Discovery & Web Scraping (P1 — Critical)

#### 3. SerpAPI (Google Maps & Search Engine Data)
- **Variable Name**: `SERPAPI_API_KEY`
- **Where to get it**: [SerpAPI Dashboard](https://serpapi.com/manage-api-key)
- **Required Permission**: Google Maps API & Google Search API access.
- **Purpose**: Automated discovery of local businesses, plumbers, clinics, agencies, and B2B companies from Google Maps and SERP queries.
- **Cost / Free Tier**: 100 free searches/month; paid plans for higher volume.

#### 4. Firecrawl API (Clean Markdown Web Scraping)
- **Variable Name**: `FIRECRAWL_API_KEY`
- **Where to get it**: [Firecrawl Dashboard](https://www.firecrawl.dev/app/api-keys)
- **Required Permission**: Web crawl and scrape endpoint access.
- **Purpose**: Deep-scraping target prospect websites, extracting company bios, tech stacks, and verifying contact emails while bypassing anti-bot blocks.
- **Cost / Free Tier**: 500 free credits on signup.

#### 5. Apify API (Bulk Actor Scraping)
- **Variable Name**: `APIFY_API_TOKEN`
- **Where to get it**: [Apify Console](https://console.apify.com/account/integrations)
- **Required Permission**: Run permission for `compass/crawler-google-places` or Google Maps actors.
- **Purpose**: High-volume asynchronous lead extraction across entire geographic regions.
- **Cost / Free Tier**: $5 free monthly tier.

---

### GROUP 3: Email Outreach & Deliverability (P1 — Critical)

#### Option A: Direct Outbound SMTP (Recommended for Quickest Setup)
- **Variable Names**:
  - `SMTP_HOST`: e.g., `smtp.gmail.com` or custom mail server host
  - `SMTP_PORT`: `587` (TLS) or `465` (SSL)
  - `SMTP_USER`: Dedicated sending email address (e.g. `outreach@yourcompany.com`)
  - `SMTP_PASSWORD`: **Google App Password** (Generated in Google Account $\to$ Security $\to$ 2-Step Verification $\to$ App Passwords)
- **Purpose**: Sending human-approved cold email sequences, newsletters, and follow-ups.

#### Option B: Google Cloud OAuth 2.0 (For Two-Way Inbox Sync)
- **Variable Names**:
  - `GMAIL_CLIENT_ID`: OAuth 2.0 Client ID (Web Application)
  - `GMAIL_CLIENT_SECRET`: OAuth 2.0 Client Secret
  - `GMAIL_REFRESH_TOKEN`: User authorized refresh token
- **Where to get it**: [Google Cloud Console $\to$ Credentials](https://console.cloud.google.com/apis/credentials)
- **Required Scopes**:
  - `https://www.googleapis.com/auth/gmail.send`
  - `https://www.googleapis.com/auth/gmail.readonly`
  - `https://www.googleapis.com/auth/gmail.modify`
- **Purpose**: Syncing incoming prospect replies into the Unified Inbox to automatically trigger stop conditions.

---

### GROUP 4: WhatsApp Business Cloud API (P2 — High)

#### 6. Meta WhatsApp Cloud API
- **Variable Names**:
  - `WHATSAPP_ACCESS_TOKEN`: Permanent System User Access Token
  - `WHATSAPP_PHONE_NUMBER_ID`: WhatsApp Sender Phone Number ID
  - `WHATSAPP_BUSINESS_ACCOUNT_ID`: WhatsApp Business Account ID (WABA ID)
  - `WHATSAPP_VERIFY_TOKEN`: Internal webhook verification string (can be custom generated)
- **Where to get it**: [Meta for Developers $\to$ WhatsApp App Dashboard](https://developers.facebook.com/apps/)
- **Required Scopes / Permissions**:
  - `whatsapp_business_messaging`
  - `whatsapp_business_management`
- **Purpose**: Sending direct 1-to-1 WhatsApp follow-ups to qualified leads and processing inbound WhatsApp replies.
- **Cost**: 1,000 free service conversations per month by Meta.

---

### GROUP 5: Multi-Platform Social Media Automation (P2 / P3)

#### 7. LinkedIn API (Personal Profile & Company Page)
- **Variable Names**:
  - `LINKEDIN_CLIENT_ID`: App Client ID
  - `LINKEDIN_CLIENT_SECRET`: App Client Secret
  - `LINKEDIN_ACCESS_TOKEN`: OAuth 2.0 Bearer Token
  - `LINKEDIN_PERSON_URN`: `urn:li:person:{id}` (Personal profile identifier)
  - `LINKEDIN_ORGANIZATION_URN`: `urn:li:organization:{id}` (Company Page identifier)
- **Where to get it**: [LinkedIn Developer Portal](https://www.linkedin.com/developers/apps)
- **Required Product & Permissions**:
  - Add product: **Share on LinkedIn** and **Sign In with LinkedIn using OpenID Connect**
  - Scopes: `w_member_social`, `r_liteprofile` (or `openid`, `profile`)
  - For Company Page: **Community Management API** with `w_organization_social`, `r_organization_social`
- **Purpose**: Autonomous and approval-based publishing of thought leadership articles, case studies, and corporate updates.

#### 8. X / Twitter API v2
- **Variable Names**:
  - `TWITTER_API_KEY`: Consumer Key (API Key)
  - `TWITTER_API_SECRET`: Consumer Secret (API Key Secret)
  - `TWITTER_ACCESS_TOKEN`: User Access Token
  - `TWITTER_ACCESS_TOKEN_SECRET`: User Access Token Secret
  - `TWITTER_BEARER_TOKEN`: App Bearer Token
- **Where to get it**: [X Developer Portal](https://developer.x.com/en/portal/dashboard)
- **Required Scopes**:
  - User Authentication Settings: Read and Write (`tweet.read`, `tweet.write`, `users.read`)
- **Purpose**: Autonomous publishing of threads, technical insights, and product build-in-public posts.
- **Tier**: Free tier allows writing up to 1,500 tweets/month; Basic tier ($100/mo) allows read/metrics.

#### 9. Instagram Content Publishing API
- **Variable Names**:
  - `INSTAGRAM_ACCESS_TOKEN`: Meta Long-Lived System User Token
  - `INSTAGRAM_BUSINESS_ACCOUNT_ID`: Instagram Professional Account ID (linked to Facebook Page)
- **Where to get it**: [Meta for Developers](https://developers.facebook.com/apps/) $\to$ Select App $\to$ Instagram Graph API.
- **Required Permissions**:
  - `instagram_basic`
  - `instagram_content_publish`
  - `pages_read_engagement`
  - `pages_show_list`
- **Purpose**: Automated container creation and publishing of visual graphics, carousel briefs, and marketing captions.

#### 10. Facebook Pages Graph API
- **Variable Names**:
  - `FACEBOOK_PAGE_ACCESS_TOKEN`: Never-expiring Page Access Token
  - `FACEBOOK_PAGE_ID`: Facebook Page Numeric ID
- **Where to get it**: [Graph API Explorer](https://developers.facebook.com/tools/explorer/) (generate Page Access Token).
- **Required Permissions**:
  - `pages_manage_posts`
  - `pages_read_engagement`
  - `pages_show_list`
- **Purpose**: Publishing status updates, announcements, and image posts directly to the corporate Facebook Page.

---

## Ready-to-Fill `.env` Template

You can copy and fill in this template as keys are received:

```ini
# ==============================================================================
# AI SALES, CRM & SOCIAL MEDIA OS — LIVE ENVIRONMENT KEYS
# ==============================================================================

# --- AI Intelligence (P1) ---
GEMINI_API_KEY=
OPENROUTER_API_KEY=

# --- Lead Discovery & Scrapers (P1) ---
SERPAPI_API_KEY=
FIRECRAWL_API_KEY=
APIFY_API_TOKEN=

# --- Outbound Email (SMTP or Google Workspace) (P1) ---
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=

# --- Gmail OAuth Two-Way Sync (P2) ---
GMAIL_CLIENT_ID=
GMAIL_CLIENT_SECRET=
GMAIL_REFRESH_TOKEN=

# --- WhatsApp Business Cloud API (P2) ---
WHATSAPP_PHONE_NUMBER_ID=
WHATSAPP_ACCESS_TOKEN=
WHATSAPP_BUSINESS_ACCOUNT_ID=
WHATSAPP_VERIFY_TOKEN=crm_secure_verify_token_2026

# --- LinkedIn API (Personal & Company Page) (P2) ---
LINKEDIN_CLIENT_ID=
LINKEDIN_CLIENT_SECRET=
LINKEDIN_ACCESS_TOKEN=
LINKEDIN_PERSON_URN=urn:li:person:
LINKEDIN_ORGANIZATION_URN=urn:li:organization:

# --- X (Twitter) API v2 (P2) ---
TWITTER_API_KEY=
TWITTER_API_SECRET=
TWITTER_ACCESS_TOKEN=
TWITTER_ACCESS_TOKEN_SECRET=
TWITTER_BEARER_TOKEN=

# --- Instagram Content Publishing API (P3) ---
INSTAGRAM_ACCESS_TOKEN=
INSTAGRAM_BUSINESS_ACCOUNT_ID=

# --- Facebook Pages Graph API (P3) ---
FACEBOOK_PAGE_ACCESS_TOKEN=
FACEBOOK_PAGE_ID=
```

---

## Quick Testing Instructions Once Keys are Received

1. Paste the received keys into the root `.env` file at `d:\MVP\.env`.
2. Verify connections in the application UI:
   - **Social Accounts**: Navigate to `Content & Social` $\to$ `Connected Accounts` tab $\to$ Click **"Verify Connection"** on each card.
   - **Email Deliverability**: Navigate to `Deliverability & DNS` $\to$ Click **"Verify DNS Records"**.
   - **Lead Discovery**: Navigate to `Lead Discovery` $\to$ Run a quick 5-lead test query.
3. Run the automated test suite to verify all integrations:
   ```bash
   backend\venv\Scripts\pytest backend\tests -v
   ```
