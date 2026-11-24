# Google Maps Scraper Engine (Autonomous Lead Generation Daemon)

High-performance, unlimited, zero-cost **Google Maps & Business Lead Scraper Engine** with automated email extraction, social media profile discovery (Instagram, LinkedIn, Facebook, X), phone normalization, and direct REST API serving.

Built with **100% Python Standard Library** — zero pip dependencies required to run the core engine!

---

## ⚡ Key Highlights (Khaasiyat)

- **Unlimited Zero-Cost Leads**: Google Maps se real-time businesses extract karta hai bina kisi paid API key (SerpAPI, Outscraper wagera ki zarurat nahi).
- **Deep Email & Social Extraction**: Business ki website ko background me crawl karke verified emails aur Facebook, Instagram, LinkedIn, X (Twitter) handles fetch karta hai.
- **Python Standard Library Only**: Na koi bhari library install karni hai, na dependency conflict ka jhanjhat.
- **Server-Ready Architecture**: VPS, Cloud Server (Ubuntu/Debian), ya Docker container me 1-click deploy ho jata hai.
- **Full REST API & Web UI**: Swagger/OpenAPI docs, CSV/JSON direct downloads, aur real-time job monitoring built-in hai.
- **CORS & Remote Host Enabled**: Remote server ya external CRM (PHP, Node.js, Python) se direct access supported hai (`SCRAPER_ALLOW_REMOTE=1`).

---

## 📁 Clean Project Structure

```text
google-map-scraper/
├── Dockerfile                  # Production Debian + Chromium container
├── docker-compose.yml          # 1-command Docker deployment
├── deploy.sh                   # 1-command Linux server installer & service generator
├── requirements.txt            # Zero core dependencies (standard library only)
├── .env.example                # Configuration template
├── engine/
│   ├── serve.py                # Core HTTP REST API Server & Web UI (Port 8080)
│   ├── maps.py                 # Google Maps CDP parsing engine
│   ├── browser.py              # Headless Chrome manager
│   ├── cdp.py                  # Chrome DevTools Protocol client
│   ├── jobs.py                 # SQLite persistent job queue & deduplication
│   ├── details.py              # Place details parser
│   ├── website_browser.py      # Website email & social profile discovery
│   └── presets/                # World cities & business category presets
├── scripts/
│   ├── engine.py               # Engine manager CLI (start, stop, status)
│   ├── leads.py                # Lead exporter CLI
│   ├── scrape.py               # Direct CLI scraper utility
│   ├── scrape.sh               # Bash launcher
│   └── google-maps-scraper.service # Linux systemd background service file
└── examples/
    ├── queries.example.json    # Batch queries template
    └── queries.example.txt     # Text queries template
```

---

## 🚀 Server Deployment (Apne Server Par Kaise Setup Karein?)

### Tarika 1: Docker ke sath (Sabse Aasan — Recommended)

Agar aapke server par Docker aur Docker Compose installed hai:

```bash
# 1. Clone ya copy folder to server
cd google-map-scraper

# 2. Config setup karein
cp .env.example .env

# 3. Background container start karein
docker compose up -d --build
```
Engine `http://your-server-ip:8080` par live ho jayega!

---

### Tarika 2: Linux Server (Ubuntu / Debian VPS) bina Docker ke

Agar aap bare VPS (DigitalOcean, AWS EC2, Hetzner, Linode) par direct run karna chahte hain:

```bash
cd google-map-scraper

# Automated Script chalayein (Chromium aur dependencies install karega):
chmod +x deploy.sh
./deploy.sh
```

#### Systemd Background Service banana (Taaki reboot par bhi automatically chale):
```bash
sudo ./deploy.sh --service
```
Ab scraper server background daemon ban gaya hai:
- **Status check**: `sudo systemctl status google-maps-scraper`
- **Restart**: `sudo systemctl restart google-maps-scraper`
- **Logs dekhna**: `sudo journalctl -u google-maps-scraper -f`

---

### Tarika 3: Manual Python Run

```bash
# Server par background run karein
export SCRAPER_ALLOW_REMOTE=1
python3 engine/serve.py --host 0.0.0.0 --port 8080 --allow-remote
```

---

## 🔌 REST API Endpoints

### 1. Create a Scraping Job
**`POST /api/v1/jobs`**

**Headers:**
- `Content-Type: application/json`
- `X-API-Key: <your_key>` *(agar .env me SCRAPER_API_KEY set hai)*

**Body:**
```json
{
  "queries": [
    "Dental Clinics in Lucknow",
    "Orthopedic Doctors in Lucknow"
  ],
  "depth": 3,
  "email": true,
  "socials": true,
  "verify_emails": true,
  "lang": "en"
}
```

**Response (HTTP 200):**
```json
{
  "id": "e8b7f83c-1b77-4b5c-890a-112233445566",
  "Status": "ok",
  "Name": "Dental Clinics in Lucknow",
  "Created": 1732440000
}
```

---

### 2. Check Job Progress
**`GET /api/v1/jobs/{job_id}`**

**Response:**
```json
{
  "id": "e8b7f83c-1b77-4b5c-890a-112233445566",
  "Status": "ok",
  "Progress": {
    "places": 48,
    "emails_found": 32,
    "queries_done": 2,
    "queries_total": 2
  }
}
```

---

### 3. Download Results (JSON / CSV)
**`GET /api/v1/jobs/{job_id}/download?format=json`**  
ya  
**`GET /api/v1/jobs/{job_id}/download?format=csv`**

Direct download link for your CRM or database pipeline!

---

## 🌐 Web UI Interface
Aap kisi bhi browser me direct engine open kar sakte hain:
`http://localhost:8080` ya `http://your-server-ip:8080`
- Interactive visual interface jahan se aap category aur city choose karke leads scan kar sakte hain.
- Direct CSV / JSON download buttons.
- Real-time live crawling progress bar.
