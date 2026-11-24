# AI Sales CRM OS — Python SDK

Official Python SDK for AI Sales CRM OS.  
Zero external dependencies (uses standard library `urllib` and `hmac`).

## 🚀 Quick Usage

```python
from aisalescrm import AiSalesCrm

crm = AiSalesCrm(base_url="http://localhost:8000")

# 1. Ingest Lead
lead = crm.ingest_lead({
    "business_name": "Dr. Batra Homeopathy",
    "phone": "+91 99887 76655",
    "email": "contact@batra.in",
    "city": "Lucknow",
})
print("Unified Lead ID:", lead["lead"]["id"])

# 2. Discover Leads via Google Maps Scraper
discovery = crm.discover_leads(query="Skin Clinics", location="Lucknow", limit=5)
for p in discovery.get("leads", []):
    print(p.get("business_name"), p.get("phone"))
```
