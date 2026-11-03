# Provider Setup Guide

This guide explains how to obtain API keys for each provider and configure them.

## Discovery Providers

### Apify (Recommended for MVP)

**Purpose:** Discover businesses from Google Maps

**Pricing:** Free tier includes $5 credit (~250 searches)
- Pay-as-you-go: $49/month for $50 credit
- Official pricing: https://apify.com/pricing

**Setup:**

1. **Create Account:**
   - Visit: https://console.apify.com/sign-up
   - Sign up with email or Google

2. **Get API Token:**
   - Go to: https://console.apify.com/account/integrations
   - Copy your API token

3. **Find Actor ID:**
   - Visit: https://apify.com/compass/crawler-google-places
   - Or use default: `nwua9Gu5YrADL7ZDj`

4. **Add to `.env`:**
```env
APIFY_API_TOKEN=apify_api_xxxxxxxxxxxxxxxxxxxxx
APIFY_MAPS_ACTOR_ID=VddE8rOIe6LNd80dw
```

**Test:**
```python
# Test in Python
import httpx

response = httpx.get(
    "https://api.apify.com/v2/store",
    params={"token": "your_token"}
)
print(response.status_code)  # Should be 200
```

---

### Outscraper (Alternative)

**Purpose:** Alternative business discovery from Google Maps

**Pricing:** Free tier includes 20 requests/month
- Starter: $29/month (400 requests)
- Official pricing: https://outscraper.com/pricing/

**Setup:**

1. **Create Account:**
   - Visit: https://outscraper.com/signup
   - Sign up with email

2. **Get API Key:**
   - Go to: https://outscraper.com/api-access/
   - Copy your API key

3. **Add to `.env`:**
```env
OUTSCRAPER_API_KEY=xxxxxxxxxxxxxxxxxxxxx
```

---

### Google Places API (Official)

**Purpose:** Official Google business data

**Pricing:** $32 per 1000 requests (Basic Data)
- Requires Google Cloud billing account
- Official pricing: https://mapsplatform.google.com/pricing/

**Setup:**

1. **Create Google Cloud Project:**
   - Visit: https://console.cloud.google.com/
   - Create new project

2. **Enable Places API:**
   - Go to: APIs & Services → Library
   - Search "Places API"
   - Click Enable

3. **Create API Key:**
   - Go to: APIs & Services → Credentials
   - Create credentials → API key
   - Restrict key to Places API

4. **Enable Billing:**
   - Go to Billing
   - Add payment method

5. **Add to `.env`:**
```env
GOOGLE_PLACES_API_KEY=AIzaxxxxxxxxxxxxxxxxxxxxx
```

**Note:** Most expensive option but most reliable.

---

## Enrichment Providers

### Firecrawl (Recommended)

**Purpose:** Extract contact information from websites

**Pricing:** Free tier includes 500 credits
- Hobby: $20/month (2,000 credits)
- Official pricing: https://www.firecrawl.dev/pricing

**Setup:**

1. **Create Account:**
   - Visit: https://www.firecrawl.dev/
   - Sign up with email or GitHub

2. **Get API Key:**
   - Go to dashboard
   - Navigate to API Keys
   - Copy your API key

3. **Add to `.env`:**
```env
FIRECRAWL_API_KEY=fc-xxxxxxxxxxxxxxxxxxxxx
```

**Test:**
```python
import httpx

response = httpx.post(
    "https://api.firecrawl.dev/v0/scrape",
    headers={"Authorization": "Bearer your_key"},
    json={"url": "https://example.com"}
)
print(response.status_code)  # Should be 200
```

---

## Search Providers (Optional)

### SerpAPI

**Purpose:** Web search for discovering business websites

**Pricing:** Free tier includes 100 searches/month
- Startup: $50/month (5,000 searches)
- Official pricing: https://serpapi.com/pricing

**Setup:**

1. **Create Account:**
   - Visit: https://serpapi.com/users/sign_up
   - Sign up with email

2. **Get API Key:**
   - Go to dashboard
   - Copy your API key

3. **Add to `.env`:**
```env
SEARCH_API_PROVIDER=serpapi
SEARCH_API_KEY=xxxxxxxxxxxxxxxxxxxxx
```

---

## Configuration Matrix

| Provider | Purpose | Free Tier | Recommended For |
|----------|---------|-----------|-----------------|
| Apify | Business Discovery | $5 credit (~250 searches) | MVP Development |
| Firecrawl | Website Enrichment | 500 credits | MVP Development |
| Outscraper | Business Discovery | 20 requests/month | Testing |
| Google Places | Business Discovery | None ($32/1000 requests) | Production |
| SerpAPI | Web Search | 100 searches/month | Optional Enhancement |

---

## Minimum Required for MVP

To run the complete MVP, you need:

1. **Apify** (Business Discovery) - Free tier sufficient
2. **Firecrawl** (Website Enrichment) - Free tier sufficient

Total cost: **$0** for initial testing with free tiers

---

## Recommended Development Setup

### Phase 1: Testing (Free Tier)
- Apify: Free $5 credit
- Firecrawl: 500 free credits
- **Cost:** $0

### Phase 2: Production (Low Volume)
- Apify: $49/month
- Firecrawl: $20/month
- **Total:** $69/month (~1,000 complete business discoveries)

### Phase 3: Production (Medium Volume)
- Apify: $149/month
- Firecrawl: $100/month
- **Total:** $249/month (~10,000 complete business discoveries)

---

## Cost Estimation

### Per Business Discovery

**Discovery Only (Maps Data):**
- Apify: ~$0.02 per business
- Outscraper: ~$0.07 per business
- Google Places: ~$0.03 per business

**Complete Enrichment (Discovery + Website + Contacts):**
- Apify + Firecrawl: ~$0.03 per business
- Total with retries: ~$0.05 per business

**Example:**
- 1,000 businesses/month: ~$50
- 5,000 businesses/month: ~$250
- 10,000 businesses/month: ~$500

---

## Fallback Strategy

If API keys are not available:

1. **Demo Mode:**
   - System shows sample data clearly labeled as demo
   - No real API calls made

2. **Basic Scraping:**
   - Firecrawl fallback to httpx + BeautifulSoup
   - Only works on permitted public pages

3. **Manual Import:**
   - CSV import for existing lead lists
   - Manual enrichment

---

## Security Best Practices

1. **Never commit `.env` files:**
```powershell
# .env is in .gitignore
git status  # Should not show .env
```

2. **Restrict API keys:**
   - Add IP restrictions where possible
   - Set usage limits
   - Rotate keys periodically

3. **Monitor usage:**
   - Set up billing alerts
   - Track API call counts
   - Review monthly costs

4. **Use environment-specific keys:**
   - Development keys for local
   - Staging keys for testing
   - Production keys for live

---

## Verification Commands

### Test All Providers

```powershell
# Activate venv
cd backend
.\venv\Scripts\activate

# Run provider tests
python -c "
from app.providers.discovery import ApifyMapsProvider
from app.providers.enrichment import FirecrawlProvider

apify = ApifyMapsProvider()
print(f'Apify configured: {apify.is_configured()}')

firecrawl = FirecrawlProvider()
print(f'Firecrawl configured: {firecrawl.is_configured()}')
"
```

### Expected Output:
```
Apify configured: True
Firecrawl configured: True
```

---

## Support Links

- Apify Support: https://docs.apify.com/
- Firecrawl Support: https://docs.firecrawl.dev/
- Outscraper Support: https://outscraper.com/faq/
- Google Places API: https://developers.google.com/maps/documentation/places/web-service/
- SerpAPI Support: https://serpapi.com/docs

---

## Next Steps

After configuration:
1. Verify all keys in `.env`
2. Restart backend server
3. Test with a real search
4. Monitor API usage in provider dashboards
