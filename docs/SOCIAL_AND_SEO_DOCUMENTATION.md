# Social Media, Content & SEO Engine Documentation

**System**: AI Sales, Lead Generation, Outreach & Marketing Operating System  
**Modules**: `ContentMarketingService`, `SEOService`, and Marketing Data Models  
**Version**: 2.0.0  

---

## 1. Overview & Strategic Goals

Inbound marketing and outbound sales reinforce each other. When a cold prospect receives an email or message, their first action is often to research the founder's LinkedIn presence, search the company's domain on Google, and review community sentiment.

The **Social Media, Content & SEO Engine** supports this GTM motion by:
1. Operationalizing a **5-Pillar Content Framework** to consistently generate thought leadership.
2. Repurposing core ideas into native formats optimized for **LinkedIn**, **X (Twitter)**, and **Reddit**.
3. Scheduling multi-platform campaigns with a clear **Simulation / Not-Configured Safety Policy**.
4. Executing inbound **SEO Keyword Clustering**, generating comprehensive **Content Briefs**, and writing high-CTR **Meta Tags**.

---

## 2. The 5 Content Marketing Pillars

All content generated in the studio is categorized under five strategic pillars:

| Pillar | Strategic Focus | Target Format & Tone | Example Topic |
|:---|:---|:---|:---|
| **1. EDUCATIONAL** | Teaching actionable tactics, frameworks, or technical guides. | In-depth breakdown, code snippets, step-by-step tutorial. | *"How to verify DNS SPF/DKIM records in Python without external SaaS tools."* |
| **2. PROBLEM-SOLVING** | Diagnosing painful industry bottlenecks and presenting concrete solutions. | Before/after comparison, root cause analysis. | *"Why 40% of B2B cold emails land in spam and how to fix your inbox warmup."* |
| **3. INDUSTRY TRENDS** | Commentary on emerging shifts, AI developments, and market data. | Data analysis, contrarian perspective, forward-looking thesis. | *"Why agentic workflows are replacing visual automation tools like n8n in 2026."* |
| **4. CASE STUDIES** | Demonstrating verifiable customer outcomes, ROI, and performance metrics. | Problem -> Implementation -> Quantifiable Results. | *"How a logistics SaaS generated 24 qualified sales calls in 3 weeks."* |
| **5. PROMOTIONAL** | Feature announcements, product launches, and direct calls to action. | Benefit-first summary, clear CTA, link to demo/meeting. | *"Announcing our new AI Sales & CRM Operating System v2.0."* |

---

## 3. Multi-Platform AI Repurposing Engine

A single input concept (such as a core insight, blog post, or feature release) is transformed by `ContentMarketingService.repurpose_content(topic, pillar)` into three distinct platform formats:

```
                                [Master Topic & Pillar]
                                           |
                    +----------------------+----------------------+
                    |                      |                      |
                    v                      v                      v
          [LinkedIn Generator]       [X / Twitter Bot]       [Reddit Formatter]
          - Attention Hook           - Thread of 3-5 tweets  - Community-first value
          - 1-sentence spacing       - Concise (<280 chars)  - Zero sales fluff
          - Professional story       - Relevant hashtags     - Open discussion prompt
          - Call for discussion      - High virality hook    - Markdown formatting
```

### Prompt Engineering Guidelines Per Platform
1. **LinkedIn Draft**: Starts with a 1-line contrarian or high-curiosity hook. Uses short, punchy paragraphs with double line breaks for readability. Concludes with an open-ended question to drive comment engagement.
2. **X / Twitter Thread**: Deconstructs the core lesson into 3 to 5 numbered tweets. Every tweet delivers standalone value under 280 characters. Includes 2-3 strategic hashtags.
3. **Reddit Post**: Formatted in Markdown (`**bold**`, bulleted lists). Strips out marketing buzzwords and self-promotional links. Focuses purely on technical or operational value and invites peer debate.

---

## 4. Content Calendar & Safety Publishing Policy

Content entries are stored in `content_calendar_entries` with fields:
- `channel`: `LINKEDIN`, `TWITTER`, `REDDIT`, `BLOG`
- `scheduled_at`: Target publication timestamp
- `status`: `DRAFT`, `SCHEDULED`, `NOT_CONFIGURED`, `PUBLISHED`, `FAILED`

### Safety Rule on Third-Party Publishing
> [!IMPORTANT]
> To preserve system integrity and avoid false claims:
> When live OAuth credentials for LinkedIn, X API v2, or Reddit OAuth are unconfigured in `.env`, the system marks scheduled entries as **`NOT_CONFIGURED`** upon execution.
> The system **never fabricates** a successful API transmission. Operators can copy the generated copy directly into platform schedulers.

---

## 5. SEO & Inbound Marketing Engine

The `SEOService` provides organic search optimization capabilities:

### 5.1. Keyword Clustering
Groups candidate keywords into functional clusters by semantic similarity, search intent, and volume:
- `INFORMATIONAL`: Top-of-funnel searches *(e.g. "what is email deliverability")*
- `COMMERCIAL`: Mid-funnel comparison searches *(e.g. "best cold email platforms 2026")*
- `TRANSACTIONAL`: Bottom-of-funnel buying intent *(e.g. "buy sales crm software")*
- `NAVIGATIONAL`: Brand-specific searches *(e.g. "antigravity crm login")*

### 5.2. AI Content Brief Generator
Generates ready-to-write briefs for content creators and copywriters:
- **Title & Primary Keyword**: Selected for search volume and ranking feasibility.
- **Heading Structure**: Comprehensive H1, H2, and H3 layout covering all search intent subtopics.
- **Target Word Count**: Recommended word length based on competitive SERP depth (typically 1,800 - 2,500 words).
- **Secondary Keywords**: Latent semantic indexing (LSI) terms to weave into the copy.

### 5.3. SERP Meta Tag Generator
Produces high-converting metadata adhering to search engine display limits:
- **Meta Title**: Strict limit of **60 characters**. Includes primary keyword near the beginning.
- **Meta Description**: Strict limit of **155-160 characters**. Summarizes value proposition and includes an action-oriented CTA.

