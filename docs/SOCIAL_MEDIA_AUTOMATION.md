# Multi-Platform Social Media Automation Manual

**System**: AI Sales, Lead Generation, Outreach & Marketing Operating System  
**Module**: Social Media Automation Engine (`SocialService`, `InstagramProvider`, `FacebookProvider`, `TwitterProvider`, `LinkedInProvider`)  
**Version**: 2.5.0  
**Updated**: November 3, 2026  
**Architecture Mandate**: STRICTLY ZERO n8n — 100% Native Python Architecture (FastAPI, Celery, Redis, SQLAlchemy 2.0)

---

## 1. Executive Summary & Supported Platforms

The Social Media Automation Engine provides end-to-end autonomous and human-in-the-loop social media management across four official platform ecosystems:

1. **Instagram**: Meta Graph API / Instagram Content Publishing API (Feed Posts & Reels/Photos).
2. **Facebook Pages**: Meta Graph API for Business Pages (Feed Status & Photo Posts).
3. **X (Twitter)**: Official X API v2 (Tweets, Threads, and Media Publishing).
4. **LinkedIn**: Official LinkedIn Posts API v2 (Personal Founder Profiles and Corporate Organization Pages).

```
+===================================================================================================+
|                              MULTI-PLATFORM SOCIAL MEDIA ENGINE                                   |
+===================================================================================================+
|                                                                                                   |
|  [Step 1: AI Research]            [Step 2: Multi-Platform Generator]  [Step 3: Creative Briefs]   |
|  - Viral Trending Angles          - Tailored Copy & Spacing           - Aspect Ratios (1:1, 16:9) |
|  - Audience Resonance Pain Points - Platform-Native Hashtags          - Headline Overlay Text     |
|  - Discovery Keywords             - Authentic Voice & CTAs            - Color Palettes            |
|                                                                                                   |
|  [Step 4: Interactive Previews]   [Step 5: Centralized Calendar]      [Step 6: Official APIs]     |
|  - Instagram Phone Mockup         - Cross-Platform Schedule           - Instagram Graph API       |
|  - Facebook Feed Card             - Real-Time Publishing Timestamps   - Facebook Page Feed        |
|  - X (Twitter) Tweet Card         - Drag/Reschedule Controls          - X API v2 Tweets           |
|  - LinkedIn Feed Post Card        - Instant "Publish Now" Option      - LinkedIn Posts API v2     |
|                                                                                                   |
|  [Step 7: Safeguards & Quality]   [Step 8: Performance Analytics]    [Step 9: Accounts Desk]     |
|  - 24-Hour Duplicate Hash Blocker - Impressions, Reach, Likes, Shares - Instagram, FB, X, LI     |
|  - Token Expiration Detection     - Engagement Rate Computation       - Health & Token Monitors   |
|  - Exception Queue Alerting       - AI Executive Summary Reports      - 1-Click Verification      |
+===================================================================================================+
```

---

## 2. Supported Platforms & Official API Integration

### 2.1. Instagram (Meta Graph API / Content Publishing API)
- **Account Type**: Instagram Business or Creator Account connected to a Facebook Page.
- **Publishing Pipeline**:
  1. **Container Creation**:
     ```http
     POST https://graph.facebook.com/v19.0/{ig_user_id}/media
     image_url={public_media_url}&caption={caption}&access_token={token}
     ```
  2. **Container Publication**:
     ```http
     POST https://graph.facebook.com/v19.0/{ig_user_id}/media_publish
     creation_id={container_id}&access_token={token}
     ```
- **Formatting Guidelines**: Visual-first storytelling, double line breaks, 10–15 curated niche hashtags, clear CTA (*"Link in bio"* or *"Save this for later"*), 1:1 square or 4:5 portrait aspect ratio.
- **Analytics Metrics**: Impressions, Reach, Likes, Comments, Shares, Saves.

### 2.2. Facebook Pages (Meta Graph API)
- **Account Type**: Facebook Business Page.
- **Publishing Pipeline**:
  - Photo Posts: `POST https://graph.facebook.com/v19.0/{page_id}/photos` with `url={image_url}`, `caption={caption}`.
  - Text/Link Posts: `POST https://graph.facebook.com/v19.0/{page_id}/feed` with `message={caption}`.
- **Formatting Guidelines**: Conversational problem-solution narrative, 3–5 broad hashtags, community question to drive comments, 1.91:1 landscape image.
- **Analytics Metrics**: Post Impressions, Engaged Users, Total Reactions by Type.

### 2.3. X / Twitter (X API v2)
- **Account Type**: X Developer App Project with Essential or Pro access.
- **Publishing Pipeline**:
  ```http
  POST https://api.twitter.com/2/tweets
  Authorization: Bearer {token}
  Content-Type: application/json

  {"text": "Your 280-character tweet copy #BuildInPublic"}
  ```
- **Formatting Guidelines**: Punchy 1-line hook, concise bullet points, 2–3 focused hashtags, maximum 280 characters per tweet, 16:9 landscape graphic.
- **Analytics Metrics**: Impressions, Retweets, Replies, Likes, Quote Tweets.

### 2.4. LinkedIn (Personal Profiles & Organization Pages)
- **Account Type**: LinkedIn Personal Profile and Corporate Organization Pages.
- **Publishing Pipeline**:
  ```http
  POST https://api.linkedin.com/rest/posts
  LinkedIn-Version: 202401
  X-Restli-Protocol-Version: 2.0.0
  Authorization: Bearer {token}
  Content-Type: application/json

  {
    "author": "urn:li:person:..." or "urn:li:organization:...",
    "commentary": "Your formatted post copy...",
    "visibility": "PUBLIC",
    "distribution": {
      "feedDistribution": "MAIN_FEED",
      "targetEntities": [],
      "thirdPartyDistributionChannels": []
    },
    "lifecycleState": "PUBLISHED",
    "isReshareDisabledByAuthor": false
  }
  ```
- **Formatting Guidelines**:
  - **Personal Profile**: Authentic founder/operator voice, scroll-stopping first sentence, short paragraphs with double spacing, concrete lessons learned, 3–5 professional hashtags.
  - **Organization Page**: Brand authority, industry leadership, team/product announcements, business value proposition.
- **Analytics Metrics**: Impressions, Engagements, Likes Summary, Comments Summary, Engagement Rate.

---

## 3. End-to-End Workflow Architecture

### Step 1: AI Topic & Trend Research
Before drafting copy, `SocialService.research_topic(topic, audience)` queries the AI router to identify:
- **3 Viral Trending Angles**: High-curiosity hooks that disrupt feed scrolling.
- **3 Audience Resonance Pain Points**: Specific challenges the target persona wants solved.
- **5–8 Discovery Hashtags**: Relevant search tags.
- **Visual Creative Theme**: Color palettes, aesthetic directions, and graphic layouts.

### Step 2: AI Multi-Platform Post & Creative Brief Generation
A single input topic is processed by `SocialService.generate_platform_posts()` to formulate tailored copy for all five channels simultaneously. Each post includes:
- Tailored caption matching the platform's specific culture and character limits.
- Curated hashtags.
- **Creative Brief**:
  - `visual_concept`: Detailed description of the accompanying visual.
  - `aspect_ratio`: Platform standard (e.g., `1:1` for Instagram, `1.91:1` for Facebook/LinkedIn, `16:9` for Twitter).
  - `dimensions`: Standard pixel resolution (e.g., `1080x1080`, `1200x630`, `1200x675`, `1200x627`).
  - `text_overlay`: High-contrast headline text to place on the graphic.
  - `color_palette`: Hex color codes matching the theme.

### Step 3: Interactive Editing & Live Preview Mockups
The system renders realistic UI preview frames:
- **Instagram Phone Frame**: Profile header, square image container, caption with "more" expansion, and engagement bar.
- **Facebook Feed Card**: Page logo, verified badge, sponsored/organic tag, and post body.
- **X Tweet Card**: Avatar, handle `@handle`, tweet text, media card, and retweet/like counts.
- **LinkedIn Post Card**: Author headline, 1st degree connection tag, post text with "see more", and reaction bar.
- **Live In-Place Editing**: Operators can modify captions, hashtags, and image URLs with immediate visual feedback before approving or publishing.

### Step 4: Centralized Content Calendar & Scheduling
Posts are scheduled across the week and stored in `social_posts`. The centralized calendar displays:
- Platform icon and account handle.
- Scheduled or confirmed published timestamp.
- Current status (`DRAFT`, `PENDING_APPROVAL`, `APPROVED`, `SCHEDULED`, `PUBLISHED`, `FAILED`).
- Direct **"Publish Now"** button for immediate on-demand dispatch.

---

## 4. The Three Automation Modes

The system operates across three distinct automation paradigms:

| Mode | Generation Behavior | Staging & Review | Publishing Execution | Best For |
|:---|:---|:---|:---|:---|
| **MANUAL** | Operator drafts or AI generates on-demand. | Created with status `DRAFT`. Operator edits copy and media manually. | Operator clicks **"Publish Now"** or schedules for a specific time. | High-stakes corporate announcements, custom creative graphics. |
| **APPROVAL-BASED** | AI researches and drafts posts based on topics or content pillars. | Created with status `PENDING_APPROVAL`. Staged in review queue. | Once operator clicks **"Approve"**, system publishes at scheduled time. | Standard business operations, founder thought leadership (Recommended). |
| **FULLY-AUTOMATED** | Scheduled Celery cron triggers active `SocialAutomationRule`. AI auto-researches and drafts. | Automatically approved and scheduled based on configured daily limits. | Celery worker `publish_scheduled_social_posts` auto-publishes when due. | High-frequency informational updates, curated tips, evergreen value shares. |

---

## 5. Safeguards, Resilience & Zero-Mock Guarantee

### 5.1. Strict Official Confirmation Requirement
> [!IMPORTANT]
> **Zero False Publishing Guarantee**:
> A post is **NEVER** marked with status `PUBLISHED` unless the official platform API returns HTTP 200/201 and provides a valid external post ID (`external_post_id`).
> If API credentials are not configured, the post provider status is set to **`NOT_CONFIGURED`**, the post status remains `DRAFT`, and the generated copy is retained for manual copy-paste.

### 5.2. Duplicate Post Prevention
Before publishing any post, the engine computes a SHA-256 fingerprint:
$$\text{Hash} = \text{SHA256}(\text{platform} + \text{caption}_{[:120]} + \text{date})$$
If an identical hash exists with status `PUBLISHED` within the preceding 24 hours, publishing is blocked with error `DUPLICATE_POST_BLOCKED` to protect brand reputation.

### 5.3. Token Expiration Detection
The engine checks `SocialAccount.token_expires_at` prior to dispatch. If expired:
1. Account status is transitioned to `EXPIRED`.
2. Post publishing is halted with error `TOKEN_EXPIRED`.
3. An urgent alert is emitted into the Centralized Exception Queue.

### 5.4. Exponential Retries & Exception Queue Routing
- Transient network or platform 5xx errors increment `retry_count` and defer execution by 15, 30, and 45 minutes.
- If a post fails after 3 retries, status becomes `FAILED` and an alert is routed to `ExceptionQueueService` (`category: "SOCIAL_PUBLISHING_ALERT"`).

---

## 6. Telemetry, Analytics & Automated Reports

The system tracks engagement data from platform APIs and aggregates:
- **Total Impressions & Reach** across all platforms.
- **Total Engagements** (Likes, Comments, Shares, Clicks).
- **Average Engagement Rate**:
  $$\text{Engagement Rate} = \left( \frac{\text{Total Engagements}}{\text{Total Impressions}} \right) \times 100$$
- **Platform Breakdown**: Post counts, impressions, and engagements per platform.
- **AI Executive Performance Report**: Synthesizes cross-platform trends and suggests tactical improvements.

---

## 7. Environment Variables Reference

Add the following official API credentials to `.env`:

```ini
# Instagram Content Publishing API
INSTAGRAM_ACCESS_TOKEN=your_meta_system_user_access_token
INSTAGRAM_BUSINESS_ACCOUNT_ID=your_instagram_business_account_id

# Facebook Pages Graph API
FACEBOOK_PAGE_ACCESS_TOKEN=your_facebook_page_access_token
FACEBOOK_PAGE_ID=your_facebook_page_id

# X (Twitter) API v2
TWITTER_API_KEY=your_x_api_key
TWITTER_API_SECRET=your_x_api_secret
TWITTER_ACCESS_TOKEN=your_x_user_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_x_user_access_token_secret
TWITTER_BEARER_TOKEN=your_x_app_bearer_token

# LinkedIn Posts API v2
LINKEDIN_CLIENT_ID=your_linkedin_client_id
LINKEDIN_CLIENT_SECRET=your_linkedin_client_secret
LINKEDIN_ACCESS_TOKEN=your_linkedin_oauth_access_token
LINKEDIN_PERSON_URN=urn:li:person:your_personal_urn_id
LINKEDIN_ORGANIZATION_URN=urn:li:organization:your_company_urn_id
```

> [!NOTE]
> If any platform credential is left unconfigured, the system operates safely in **`NOT_CONFIGURED` Mode**, allowing AI generation, creative brief creation, and manual copy-paste publishing without system errors.

