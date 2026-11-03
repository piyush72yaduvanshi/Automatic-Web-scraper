# System Architecture - CRM Lead Discovery Engine

## Overview

The CRM Lead Discovery Engine is a modular, provider-independent platform for discovering businesses and enriching their contact information from publicly available data.

## High-Level Architecture

```
┌─────────────┐
│   Frontend  │ React + TypeScript + Vite
│  Dashboard  │
└──────┬──────┘
       │ HTTP/REST
       ▼
┌─────────────┐
│   FastAPI   │ Python 3.11+
│  REST API   │
└──────┬──────┘
       │
       ├──► Discovery Providers
       │    ├─ Apify Maps
       │    ├─ Outscraper
       │    └─ Google Places
       │
       ├──► Enrichment Provider
       │    └─ Firecrawl + Extractors
       │
       ├──► Database Layer
       │    └─ PostgreSQL
       │
       └──► Background Jobs
            └─ Celery + Redis (Optional for MVP)
```

## Core Components

### 1. API Layer (`app/api/v1/`)

**Purpose:** RESTful API endpoints

**Routes:**
- `/health` - Service health check
- `/stats` - Platform statistics
- `/discovery/jobs` - Create and manage discovery jobs
- `/leads` - List, filter, and export leads
- `/leads/{id}` - Get lead details
- `/leads/{id}/enrich` - Enrich single lead

**Technology:**
- FastAPI for high performance
- Pydantic v2 for validation
- CORS middleware for frontend access

### 2. Service Layer (`app/services/`)

**Purpose:** Business logic and orchestration

**Services:**

**DiscoveryService:**
- Create discovery jobs
- Execute provider searches
- Coordinate enrichment
- Update job status

**LeadService:**
- Create/update leads
- List with filters
- Add enrichment data
- Deduplicate records

### 3. Provider Layer (`app/providers/`)

**Purpose:** External API integrations

**Design Pattern:** Strategy Pattern

**Discovery Providers (`discovery/`):**
- `BaseDiscoveryProvider` - Abstract interface
- `ApifyMapsProvider` - Google Maps via Apify
- Easily add: `OutscraperProvider`, `GooglePlacesProvider`

**Enrichment Providers (`enrichment/`):**
- `FirecrawlProvider` - Website content extraction
- Fallback to httpx + BeautifulSoup

**Key Features:**
- Provider-agnostic business schema
- Automatic normalization
- Configuration checks
- Error handling

### 4. Extractor Layer (`app/extractors/`)

**Purpose:** Parse and extract contact data

**Extractors:**

**EmailExtractor:**
- Extract from mailto: links
- Extract from HTML patterns
- Validate format
- Exclude placeholders

**PhoneExtractor:**
- Extract from tel: links
- Extract from text patterns
- Normalize using phonenumbers library
- Support international formats

**SocialExtractor:**
- Extract Instagram, LinkedIn, Facebook, X
- Normalize URLs
- Filter personal profiles
- Deduplicate

### 5. Data Models (`app/models/`)

**Purpose:** SQLAlchemy ORM models

**Core Models:**

```python
BusinessLead
├─ id: UUID
├─ business_name
├─ category
├─ location (city, state, country)
├─ website
├─ source_provider
└─ status

LeadContact
├─ lead_id (FK)
├─ contact_type (EMAIL/PHONE)
├─ original_value
├─ normalized_value
├─ verification_status
└─ source_url

LeadSocialProfile
├─ lead_id (FK)
├─ platform (INSTAGRAM/LINKEDIN/FACEBOOK/X)
├─ profile_url
├─ verification_status
└─ source_url

DiscoveryJob
├─ search_query
├─ location
├─ provider
├─ status (QUEUED/RUNNING/COMPLETED/FAILED)
├─ total_found
└─ total_enriched
```

### 6. Database Layer

**Technology:** PostgreSQL 14+

**Features:**
- UUID primary keys
- Foreign key constraints with CASCADE
- Indexes on frequently queried columns
- Composite indexes for complex queries
- Enum types for status fields

**Indexes:**
- `business_name`, `category`, `city` - Filtering
- `created_at` - Sorting
- `normalized_value` - Contact deduplication
- Composite: `(business_name, city)`, `(category, city)`

## Data Flow

### Discovery Flow

```
1. User submits search
   ↓
2. API creates DiscoveryJob (QUEUED)
   ↓
3. Background task starts
   ↓
4. Job status → RUNNING
   ↓
5. Provider discovers businesses
   ↓
6. For each business:
   ├─ Save BusinessLead
   ├─ If website exists:
   │  ├─ Enrich website
   │  ├─ Extract emails
   │  ├─ Extract phones
   │  └─ Extract socials
   └─ Save enrichment data
   ↓
7. Job status → COMPLETED
   ↓
8. Return to user
```

### Enrichment Flow

```
1. Get business website
   ↓
2. Crawl key pages:
   ├─ Homepage
   ├─ /contact
   ├─ /contact-us
   ├─ /about
   └─ /about-us
   ↓
3. For each page:
   ├─ Extract emails
   ├─ Extract phones
   └─ Extract social URLs
   ↓
4. Deduplicate results
   ↓
5. Save to database
   ↓
6. Update lead status
```

## Security Architecture

### SSRF Protection

```python
is_safe_url(url)
├─ Check scheme (http/https only)
├─ Block localhost/127.0.0.1
├─ Block private IP ranges (192.168.x.x, 10.x.x.x)
├─ Block cloud metadata (169.254.169.254)
└─ Block link-local addresses
```

**Implementation:** `app/core/security.py`

**Applied:**
- All website enrichment
- All external HTTP requests
- URL validation before crawling

### API Key Security

**Storage:**
- Environment variables only
- Never in code or version control
- .env in .gitignore

**Access:**
- Backend only
- Never exposed to frontend
- Provider-specific validation

### Rate Limiting

**Planned:**
- Per-IP rate limits
- Per-user quotas
- Provider-level throttling

## Scalability Considerations

### Current MVP Scale

- **Concurrent Users:** 10-20
- **Leads/Day:** 1,000-5,000
- **Database Size:** 1-10 GB
- **API Requests/min:** 100-200

### Scaling Strategies

**Horizontal Scaling:**
1. Multiple API instances behind load balancer
2. Read replicas for PostgreSQL
3. Redis cluster for caching

**Background Processing:**
1. Celery workers for job execution
2. Separate worker pools for discovery vs enrichment
3. Priority queues for urgent jobs

**Database Optimization:**
1. Partitioning by date for `business_leads`
2. Materialized views for analytics
3. Connection pooling

**Caching Layer:**
1. Redis for job status
2. Cache frequent queries
3. API response caching

## Integration Points

### Future CRM Integration

**Approach:** REST API + Webhook

**Export to CRM:**
```
GET /api/v1/leads?format=crm
└─ Returns leads in CRM-compatible format
```

**Webhook Support:**
```
POST /webhooks/lead-discovered
└─ Notify CRM of new leads
```

**Batch Operations:**
```
POST /api/v1/leads/export/crm
{
  "lead_ids": ["uuid1", "uuid2"],
  "crm_account_id": "account_123"
}
```

### Provider Extension

**Add New Discovery Provider:**

1. Create class extending `BaseDiscoveryProvider`
2. Implement required methods
3. Register in provider factory
4. Add to `.env.example`

Example:

```python
class NewProvider(BaseDiscoveryProvider):
    def discover_businesses(self, query, location, radius, limit):
        # Call provider API
        # Normalize results
        return normalized_businesses
    
    def normalize_business(self, raw_data):
        return {
            "business_name": ...,
            "category": ...,
            # etc.
        }
```

## Monitoring & Observability

### Logging

**Levels:**
- ERROR: Provider failures, validation errors
- WARNING: Rate limits, missing data
- INFO: Job status changes, API calls
- DEBUG: Detailed execution flow

**Format:** Structured JSON for parsing

### Metrics (Future)

**Track:**
- API response times
- Provider success rates
- Enrichment completion rates
- Database query performance
- Error rates by type

**Tools:** Prometheus + Grafana

### Health Checks

**Endpoint:** `/health`

**Checks:**
- Database connectivity
- Redis availability
- Provider API status

## Error Handling

### Provider Failures

**Strategy:** Graceful degradation

```python
try:
    results = await provider.discover_businesses(...)
except ProviderError:
    # Mark job as failed
    # Store error message
    # Don't retry automatically
```

### Enrichment Failures

**Strategy:** Partial success

```python
# If website crawl fails for one business
# Continue with other businesses
# Log individual failures
# Report partial results
```

### Database Errors

**Strategy:** Transaction rollback

```python
try:
    db.add(lead)
    db.commit()
except IntegrityError:
    db.rollback()
    # Handle duplicate
```

## Performance Optimization

### Database Queries

**Optimization:**
- Use indexes
- Limit result sets
- Use EXISTS for filtering
- Batch inserts

**Example:**
```python
# Bad
for item in items:
    db.add(Model(data=item))
    db.commit()

# Good
db.bulk_insert_mappings(Model, items)
db.commit()
```

### API Response Times

**Target:**
- Health check: < 100ms
- List leads: < 500ms
- Create job: < 200ms
- Job status: < 100ms

**Techniques:**
- Pagination
- Select only needed columns
- Background processing for slow operations

## Testing Strategy

### Unit Tests

**Coverage:**
- Extractors
- Security functions
- Normalization logic

### Integration Tests

**Coverage:**
- API endpoints
- Database operations
- Provider mocking

### Manual Testing

**Scenarios:**
- Real provider API calls
- End-to-end discovery flow
- Error handling

## Deployment Architecture

### Development

```
Laptop/Desktop
├─ PostgreSQL (local)
├─ Redis (local)
├─ Backend (port 8000)
└─ Frontend (port 5173)
```

### Production (Future)

```
Load Balancer
├─ API Servers (N instances)
│  └─ Docker containers
├─ Worker Servers
│  └─ Celery workers
├─ Database
│  ├─ Primary (write)
│  └─ Replicas (read)
└─ Cache
   └─ Redis Cluster
```

## Technology Choices

| Component | Technology | Justification |
|-----------|-----------|---------------|
| API Framework | FastAPI | High performance, async, OpenAPI docs |
| Database | PostgreSQL | ACID, complex queries, JSON support |
| ORM | SQLAlchemy 2 | Mature, flexible, good performance |
| Validation | Pydantic v2 | Type safety, serialization |
| HTTP Client | httpx | Async, modern |
| Phone Parsing | phonenumbers | Google's official library |
| Background Jobs | Celery | Industry standard, proven |
| Cache/Queue | Redis | Fast, versatile |
| Frontend | React | Component-based, ecosystem |
| Build Tool | Vite | Fast, modern, HMR |

## Future Enhancements

1. **Multi-tenancy:** Add company_id for SaaS
2. **Webhooks:** Real-time notifications
3. **Email Verification:** Validate deliverability
4. **Phone Verification:** Check if numbers work
5. **AI Enrichment:** Use LLMs for categorization
6. **Bulk Operations:** Import/export at scale
7. **Analytics Dashboard:** Business insights
8. **API Rate Limiting:** Protect resources
9. **GraphQL API:** Alternative to REST
10. **Mobile App:** React Native frontend
