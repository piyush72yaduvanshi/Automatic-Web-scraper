# API Keys & Credentials Request Document

**Project**: AI Sales, Lead Generation, Outreach & Social Media Operating System  
**Prepared For**: Team Lead (TL) / Engineering Management / DevOps  
**Date**: November 2026  
**Document Purpose**: Consolidated access and credential request for live third-party APIs across AI Intelligence, Google Maps Local Lead Discovery, Web Scraping, Email Infrastructure, WhatsApp, and Multi-Platform Social Media Automation.

---

## Ready-to-Send Message for Team Lead (TL)

> **Subject**: Access & API Credentials Request for AI Sales & CRM Operating System
>
> Hi **[TL Name]**,
>
> We have completed the implementation and testing of our **AI Sales, CRM, Outreach & Social Media Operating System** (all 54 backend automated tests passing, frontend production build verified).
>
> Filhaal system offline/simulation mode me gracefully run ho raha hai. Live Google Maps local business scraping, AI intelligence, automated email sequences, WhatsApp, aur social media publishing ko activate karne ke liye hume niche diye gaye API credentials aur keys ki requirement hai.
>
> Maine inko priority order me categorize kar diya hai:
> - **Priority 1 (Critical — Core Operations)**:
>   1. **Google Maps Platform / Places API Key** (`GOOGLE_PLACES_API_KEY` / `GOOGLE_MAPS_API_KEY`) — Direct local business lead discovery from Google Maps.
>   2. **Google Gemini API Key** (`GEMINI_API_KEY`) — Core AI reasoning, research, ICP qualification, cold email copywriting.
>   3. **OpenRouter API Key** (`OPENROUTER_API_KEY`) — Secondary failover AI provider (Claude 3.5 Sonnet, GPT-4o).
>   4. **SerpAPI Key** (`SERPAPI_API_KEY`) — Google Maps local pack search & SERP scraper.
>   5. **Firecrawl Key** (`FIRECRAWL_API_KEY`) — Company website deep-scraping for tech stacks & verified emails.
>   6. **Outbound Email SMTP** (`SMTP_USER`, `SMTP_PASSWORD`) — Cold email sequences & follow-ups.
> - **Priority 2 (High — Direct Customer Communication & Socials)**:
>   1. **Meta WhatsApp Cloud API** (`WHATSAPP_ACCESS_TOKEN`, `PHONE_NUMBER_ID`) — WhatsApp business messaging & replies.
>   2. **LinkedIn API** (`LINKEDIN_ACCESS_TOKEN`, Personal & Org URNs) — Automated publishing on Founder profile & Company page.
>   3. **X (Twitter) API v2** (`TWITTER_API_KEY`, User Tokens, Bearer Token) — Automated tweet & thread publishing.
>   4. **Apify API Token** (`APIFY_API_TOKEN`) — Bulk Google Maps regional scraper actor.
>   5. **Gmail OAuth Client** (`GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`) — Two-way inbox synchronization.
> - **Priority 3 (Medium — Visual & Corporate Channels)**:
>   1. **Instagram Content Publishing API** (`INSTAGRAM_ACCESS_TOKEN`, `BUSINESS_ACCOUNT_ID`).
>   2. **Facebook Pages Graph API** (`FACEBOOK_PAGE_ACCESS_TOKEN`, `PAGE_ID`).
>
> Kripya ek baar review karke in keys ka access provide kar dijiye taaki hum live production setup complete kar sakein. Detailed breakdown, exact portal links, and required permissions niche diye gaye hain.
>
> Thanks & Regards,  
> **[Your Name]**

---

## Summary Matrix of Required Keys

| # | Environment Variable | Service / Provider | Priority | Purpose |
|:---:|:---|:---|:---:|:---|
| **1** | **`GOOGLE_PLACES_API_KEY`** *(or `GOOGLE_MAPS_API_KEY`)* | **Google Maps Platform (GCP)** | **P1 (Critical)** | **Direct Google Maps local business discovery (Phones, Addresses, Ratings, Websites, Place IDs)** |
| 2 | `GEMINI_API_KEY` | Google AI Studio / Vertex AI | **P1 (Critical)** | Core AI reasoning, research, ICP qualification, cold email copywriting |
| 3 | `OPENROUTER_API_KEY` | OpenRouter | **P1 (Critical)** | Secondary failover AI provider (Claude 3.5 Sonnet, GPT-4o) |
| 4 | `SERPAPI_API_KEY` | SerpAPI | **P1 (Critical)** | Fast Google Maps local pack search & search engine scraper |
| 5 | `FIRECRAWL_API_KEY` | Firecrawl | **P1 (Critical)** | Clean web scraping of company websites to extract tech stacks & emails |
| 6 | `SMTP_USER` & `SMTP_PASSWORD` *(or Gmail OAuth)* | Google Workspace / SMTP | **P1 (Critical)** | Live cold email outreach & transactional sequence dispatch |
| 7 | `APIFY_API_TOKEN` | Apify | **P2 (High)** | High-volume Google Maps Scraper actor for bulk regional lead extraction |
| 8 | `WHATSAPP_ACCESS_TOKEN` & `PHONE_NUMBER_ID` | Meta WhatsApp Cloud API | **P2 (High)** | Omnichannel WhatsApp business messaging & reply ingestion |
| 9 | `LINKEDIN_ACCESS_TOKEN` & URNs | LinkedIn Developer Portal | **P2 (High)** | Automated posting to LinkedIn Personal Profile & Company Page |
| 10 | `TWITTER_API_KEY`, `ACCESS_TOKEN` & `BEARER_TOKEN` | X (Twitter) Developer Portal | **P2 (High)** | Automated tweet & thread publishing via X API v2 |
| 11 | `GMAIL_CLIENT_ID` & `GMAIL_CLIENT_SECRET` | Google Cloud Console | **P2 (High)** | Two-way Gmail inbox sync & unified thread monitoring |
| 12 | `INSTAGRAM_ACCESS_TOKEN` & `BUSINESS_ACCOUNT_ID` | Meta Graph API | **P3 (Medium)** | Instagram feed post & visual creative publishing |
| 13 | `FACEBOOK_PAGE_ACCESS_TOKEN` & `PAGE_ID` | Meta Graph API | **P3 (Medium)** | Facebook Corporate Page feed publishing |

---

## Detailed Credential Breakdown & Acquisition Guides

---

### GROUP 1: Google Maps Local Business Discovery & Scraping (P1 — Critical)

#### 1. Official Google Maps Platform / Places API Key
- **Variable Names**: `GOOGLE_PLACES_API_KEY` (or `GOOGLE_MAPS_API_KEY`)
- **Where to get it**: [Google Cloud Console $\to$ Google Maps Platform](https://console.cloud.google.com/google/maps-apis)
- **Required APIs to Enable in Google Cloud Console**:
  1. **Places API (New)** & **Places API** (Places Text Search & Place Details)
  2. **Geocoding API** (Converts city/locality/zip code into latitude/longitude coordinates for radius searches)
  3. **Maps JavaScript API** (For displaying interactive maps and pin markers in UI)
- **Purpose**:
  - Direct, official extraction of local business leads from Google Maps without middleman SaaS tools.
  - Retrieves verified business phone numbers, formatted addresses, Google star ratings, total review counts, websites, business operating statuses, and official Google Place IDs.
- **Cost / Free Tier**:
  - **Google Cloud provides a recurring $200 free monthly credit** for Google Maps Platform every month automatically.
  - This $200 free credit covers approximately **28,500 Places Text Searches** or **40,000 Geocoding requests** per month at zero cost.

#### 2. SerpAPI (Google Maps Local Pack Scraper)
- **Variable Name**: `SERPAPI_API_KEY`
- **Where to get it**: [SerpAPI Dashboard](https://serpapi.com/manage-api-key)
- **Required Permission**: Access to `engine=google_maps` and `engine=google`.
- **Purpose**:
  - Fast search engine scraper parsing the Google Maps local pack (3-pack and map lists).
  - Acts as a complementary scraper to capture competitor clusters and localized ranking results.
- **Cost / Free Tier**: 100 free searches/month; paid plans for higher volume.

#### 3. Apify (Bulk Regional Google Maps Actor)
- **Variable Name**: `APIFY_API_TOKEN`
- **Where to get it**: [Apify Console](https://console.apify.com/account/integrations)
- **Required Permission**: Access to run `compass/crawler-google-places` or Google Maps scraper actors.
- **Purpose**:
  - High-volume background batch discovery across entire metropolitan regions or bounding boxes.
- **Cost / Free Tier**: $5 free monthly tier.

#### 4. Firecrawl API (Company Website Scraper)
- **Variable Name**: `FIRECRAWL_API_KEY`
- **Where to get it**: [Firecrawl Dashboard](https://www.firecrawl.dev/app/api-keys)
- **Required Permission**: Web crawl and scrape endpoint access.
- **Purpose**:
  - Deep-scraping target prospect websites found on Google Maps, extracting company bios, tech stacks, and verifying contact emails while bypassing anti-bot blocks.
- **Cost / Free Tier**: 500 free credits on signup.

---

### GROUP 2: AI Intelligence Providers (P1 — Critical)

#### 5. Google Gemini API
- **Variable Name**: `GEMINI_API_KEY`
- **Where to get it**: [Google AI Studio](https://aistudio.google.com/app/apikey) or Google Cloud Console (Vertex AI).
- **Required Permission**: Standard API Access to `gemini-1.5-pro` and `gemini-1.5-flash`.
- **Purpose**: Powering the 15 specialized AI agents (Lead Research, ICP Scoring, Email Copywriting, Social Repurposing, Meeting Dossiers).
- **Cost / Free Tier**: Generous free tier (up to 15 RPM free on AI Studio); pay-as-you-go thereafter.

#### 6. OpenRouter API (Failover Provider)
- **Variable Name**: `OPENROUTER_API_KEY`
- **Where to get it**: [OpenRouter Dashboard](https://openrouter.ai/keys)
- **Required Permission**: Account API Key with access to `anthropic/claude-3.5-sonnet` and `openai/gpt-4o`.
- **Purpose**: Automatic zero-crash failover when primary AI provider experiences rate-limiting or latency spikes.
- **Cost**: Pay-as-you-go credit balance ($5–$10 deposit is sufficient for thousands of calls).

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

#### 7. Meta WhatsApp Cloud API
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

#### 8. LinkedIn API (Personal Profile & Company Page)
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

#### 9. X / Twitter API v2
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

#### 10. Instagram Content Publishing API
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

#### 11. Facebook Pages Graph API
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
# AI SALES, CRM, GOOGLE MAPS & SOCIAL MEDIA OS — LIVE ENVIRONMENT KEYS
# ==============================================================================

# --- Official Google Maps Platform / Places API (P1 - Critical) ---
GOOGLE_PLACES_API_KEY=
GOOGLE_MAPS_API_KEY=

# --- Lead Discovery & Scrapers (P1 - Critical) ---
SERPAPI_API_KEY=
FIRECRAWL_API_KEY=
APIFY_API_TOKEN=

# --- AI Intelligence (P1 - Critical) ---
GEMINI_API_KEY=
OPENROUTER_API_KEY=

# --- Outbound Email (SMTP or Google Workspace) (P1 - Critical) ---
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

# --- MinIO S3-Compatible Object Storage (Docker Image: minio/minio) ---
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin_secret_key
MINIO_BUCKET_NAME=crm-assets
MINIO_SECURE=false
MINIO_PUBLIC_URL=http://localhost:9000

# --- PostgreSQL with pgvector Vector DB (Docker Image: pgvector/pgvector:pg16) ---
PGVECTOR_ENABLED=true
VECTOR_DIMENSION=768
```

---

## How Google Maps Local Discovery Works in the Architecture

Our system supports **3 distinct ways** to pull local business leads from Google Maps:

```
                                [Discovery Orchestrator]
                                           |
                 +-------------------------+-------------------------+
                 |                         |                         |
                 v                         v                         v
     [Official Google Places API]     [SerpAPI Google Maps]     [Apify Maps Scraper]
     GOOGLE_PLACES_API_KEY            SERPAPI_API_KEY           APIFY_API_TOKEN
     - Direct Google Cloud API        - Scrapes Google Maps     - Bulk regional actor
     - Verified phone numbers         - Real local pack SERP    - Asynchronous batch runs
     - Addresses & Place IDs          - Competitor clusters     - Thousands of rows
     - $200 free credit/month         - Fast synchronous query  - Cloud webhook callback
```

Whenever the operator runs a query like `"Dentists in Chicago"` or `"Plumbing companies in Dallas"`, the system can query Google Maps directly via **Google Places API**, or fall back to **SerpAPI / Apify**, deduplicating and enriching every lead with website scraping.
