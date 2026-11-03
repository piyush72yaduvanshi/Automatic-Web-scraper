# API Documentation

Base URL: `http://localhost:8000/api/v1`

## Interactive Documentation

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## Authentication

Currently, the MVP does not require authentication. Future versions will implement JWT-based authentication.

## Endpoints

### Health & Status

#### `GET /health`

Check service health.

**Response:**
```json
{
  "status": "healthy",
  "database": "healthy",
  "redis": "healthy",
  "version": "1.0.0"
}
```

#### `GET /stats`

Get platform statistics.

**Response:**
```json
{
  "total_leads": 1523,
  "total_jobs": 45,
  "emails_found": 892,
  "phones_found": 1205,
  "social_profiles_found": 734,
  "jobs_completed": 42,
  "jobs_failed": 2,
  "jobs_running": 1
}
```

---

### Discovery Jobs

#### `POST /discovery/jobs`

Create a new business discovery job.

**Request Body:**
```json
{
  "query": "dentists",
  "location": "Lucknow, India",
  "radius_km": 10,
  "limit": 50,
  "sources": ["maps"],
  "enrich_emails": true,
  "enrich_phones": true,
  "enrich_socials": true,
  "preferred_provider": "apify"
}
```

**Parameters:**
- `query` (required): Business category or keyword
- `location` (required): City, state, country
- `radius_km` (optional): Search radius in kilometers (0-100)
- `limit` (optional): Maximum results (1-500, default: 50)
- `sources` (optional): Discovery sources (default: ["maps"])
- `enrich_emails` (optional): Extract emails (default: true)
- `enrich_phones` (optional): Extract phones (default: true)
- `enrich_socials` (optional): Extract socials (default: true)
- `preferred_provider` (optional): Provider name (apify, outscraper, google_places)

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "search_query": "dentists",
  "location": "Lucknow, India",
  "radius_km": 10,
  "requested_limit": 50,
  "provider": "apify",
  "status": "QUEUED",
  "total_found": 0,
  "total_enriched": 0,
  "created_at": "2024-01-15T10:30:00Z",
  "completed_at": null
}
```

#### `GET /discovery/jobs/{job_id}`

Get job status and details.

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "search_query": "dentists",
  "location": "Lucknow, India",
  "radius_km": 10,
  "requested_limit": 50,
  "provider": "apify",
  "provider_job_id": "apify_run_abc123",
  "status": "COMPLETED",
  "total_found": 48,
  "total_enriched": 42,
  "error_message": null,
  "created_at": "2024-01-15T10:30:00Z",
  "completed_at": "2024-01-15T10:35:30Z"
}
```

**Job Status Values:**
- `QUEUED`: Job created, waiting to start
- `RUNNING`: Job is currently executing
- `COMPLETED`: Job finished successfully
- `FAILED`: Job failed (check error_message)
- `CANCELLED`: Job was cancelled

#### `GET /discovery/jobs`

List discovery jobs with pagination.

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Items per page (1-100, default: 20)
- `status` (optional): Filter by status

**Response:**
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "search_query": "dentists",
      "location": "Lucknow, India",
      "status": "COMPLETED",
      "total_found": 48,
      "total_enriched": 42,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 45,
  "page": 1,
  "page_size": 20,
  "total_pages": 3
}
```

---

### Leads

#### `GET /leads`

List business leads with filtering and pagination.

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Items per page (1-100, default: 20)
- `search` (optional): Search in business name and category
- `category` (optional): Filter by category
- `city` (optional): Filter by city
- `has_email` (optional): Filter by email availability (true/false)
- `has_phone` (optional): Filter by phone availability (true/false)
- `has_social` (optional): Filter by social profile availability (true/false)

**Example:**
```
GET /leads?city=Lucknow&has_email=true&page=1&page_size=20
```

**Response:**
```json
{
  "items": [
    {
      "id": "650e8400-e29b-41d4-a716-446655440001",
      "business_name": "ABC Dental Clinic",
      "category": "Dentist",
      "description": "Professional dental care services",
      "address": "123 Main Street",
      "city": "Lucknow",
      "state": "Uttar Pradesh",
      "country": "India",
      "website": "https://abcdental.com",
      "source_provider": "apify",
      "status": "enriched",
      "email_count": 2,
      "phone_count": 3,
      "social_count": 4,
      "created_at": "2024-01-15T10:32:15Z",
      "updated_at": "2024-01-15T10:33:45Z"
    }
  ],
  "total": 48,
  "page": 1,
  "page_size": 20,
  "total_pages": 3
}
```

#### `GET /leads/{lead_id}`

Get detailed lead information.

**Response:**
```json
{
  "id": "650e8400-e29b-41d4-a716-446655440001",
  "business_name": "ABC Dental Clinic",
  "category": "Dentist",
  "description": "Professional dental care services",
  "address": "123 Main Street",
  "city": "Lucknow",
  "state": "Uttar Pradesh",
  "country": "India",
  "website": "https://abcdental.com",
  "source_provider": "apify",
  "status": "enriched",
  "created_at": "2024-01-15T10:32:15Z",
  "updated_at": "2024-01-15T10:33:45Z",
  "contacts": [
    {
      "id": "750e8400-e29b-41d4-a716-446655440002",
      "contact_type": "EMAIL",
      "original_value": "info@abcdental.com",
      "normalized_value": "info@abcdental.com",
      "verification_status": "unverified",
      "source_url": "https://abcdental.com/contact",
      "collected_at": "2024-01-15T10:33:20Z"
    },
    {
      "id": "750e8400-e29b-41d4-a716-446655440003",
      "contact_type": "PHONE",
      "original_value": "+91 9876543210",
      "normalized_value": "+919876543210",
      "verification_status": "unverified",
      "source_url": "https://abcdental.com",
      "collected_at": "2024-01-15T10:33:20Z"
    }
  ],
  "social_profiles": [
    {
      "id": "850e8400-e29b-41d4-a716-446655440004",
      "platform": "INSTAGRAM",
      "profile_url": "https://www.instagram.com/abcdental/",
      "verification_status": "unverified",
      "source_url": "https://abcdental.com",
      "collected_at": "2024-01-15T10:33:25Z"
    },
    {
      "id": "850e8400-e29b-41d4-a716-446655440005",
      "platform": "FACEBOOK",
      "profile_url": "https://www.facebook.com/abcdental/",
      "verification_status": "unverified",
      "source_url": "https://abcdental.com",
      "collected_at": "2024-01-15T10:33:25Z"
    }
  ]
}
```

#### `POST /leads/{lead_id}/enrich`

Enrich a single lead.

**Response:**
```json
{
  "message": "Lead enriched successfully",
  "lead_id": "650e8400-e29b-41d4-a716-446655440001"
}
```

**Error Response (400):**
```json
{
  "detail": "Lead has no website to enrich"
}
```

#### `GET /leads/export/csv`

Export leads to CSV format.

**Query Parameters:** Same as `GET /leads`

**Response:** CSV file download

```csv
business_name,category,address,city,state,country,website,email_count,phone_count,social_count,source_provider,created_at
ABC Dental Clinic,Dentist,"123 Main Street",Lucknow,Uttar Pradesh,India,https://abcdental.com,2,3,4,apify,2024-01-15T10:32:15Z
```

---

## Error Responses

### 400 Bad Request

```json
{
  "detail": "Validation error message"
}
```

### 404 Not Found

```json
{
  "detail": "Resource not found"
}
```

### 500 Internal Server Error

```json
{
  "detail": "Internal server error message"
}
```

---

## Rate Limiting

Currently not implemented in MVP. Future versions will include:
- 60 requests per minute per IP
- 1000 requests per day per user

---

## Examples

### Complete Discovery Flow

```python
import httpx
import time

# 1. Create discovery job
response = httpx.post(
    "http://localhost:8000/api/v1/discovery/jobs",
    json={
        "query": "dentists",
        "location": "Lucknow, India",
        "limit": 20,
        "enrich_emails": True,
        "enrich_phones": True,
        "enrich_socials": True
    }
)
job = response.json()
job_id = job["id"]

# 2. Poll for completion
while True:
    response = httpx.get(f"http://localhost:8000/api/v1/discovery/jobs/{job_id}")
    job = response.json()
    
    if job["status"] in ["COMPLETED", "FAILED"]:
        break
    
    print(f"Status: {job['status']}, Found: {job['total_found']}")
    time.sleep(5)

# 3. Get leads
if job["status"] == "COMPLETED":
    response = httpx.get(
        "http://localhost:8000/api/v1/leads",
        params={"city": "Lucknow", "page_size": 50}
    )
    leads = response.json()
    print(f"Total leads: {leads['total']}")
```

### Filter Leads

```python
# Get leads with emails in Lucknow
response = httpx.get(
    "http://localhost:8000/api/v1/leads",
    params={
        "city": "Lucknow",
        "has_email": True,
        "page": 1,
        "page_size": 20
    }
)

# Search for specific category
response = httpx.get(
    "http://localhost:8000/api/v1/leads",
    params={
        "search": "dental",
        "has_phone": True
    }
)
```

### Export to CSV

```python
response = httpx.get(
    "http://localhost:8000/api/v1/leads/export/csv",
    params={"city": "Lucknow", "has_email": True}
)

with open("leads.csv", "wb") as f:
    f.write(response.content)
```

---

## Webhooks (Future)

Planned webhook endpoints for real-time notifications:

- `job.started` - Discovery job started
- `job.completed` - Discovery job completed
- `job.failed` - Discovery job failed
- `lead.discovered` - New lead discovered
- `lead.enriched` - Lead enriched with contacts

---

## API Versioning

Current version: `v1`

Future versions will be backward compatible or released as `v2`, `v3`, etc.

---

## Support

For API issues or questions:
1. Check interactive documentation at `/docs`
2. Review error messages
3. Check provider configuration
4. Open an issue on GitHub
