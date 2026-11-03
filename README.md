# CRM Lead Generation & Discovery Engine - MVP

A comprehensive lead generation and business discovery platform that helps discover businesses, enrich contact information, and extract social profiles from publicly available data.

## Overview

This platform allows users to search for businesses by category, location, and radius, then automatically enriches the results with:

- Business contact information (phone, email)
- Social media profiles (Instagram, LinkedIn, Facebook, X)
- Website information
- Address and location details
- Business category and description

## Technology Stack

### Backend
- **Python 3.11+** - Core language
- **FastAPI** - High-performance API framework
- **PostgreSQL** - Primary database
- **SQLAlchemy 2** - ORM with async support
- **Alembic** - Database migrations
- **Pydantic v2** - Data validation
- **Celery + Redis** - Background job processing
- **httpx** - Async HTTP client
- **BeautifulSoup4** - HTML parsing
- **Playwright** - Browser automation (when needed)

### Frontend
- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **Lucide React** - Icons

### Integrations
- **Apify** - Business discovery from Google Maps
- **Firecrawl** - Website content extraction
- **Outscraper** - Alternative business discovery
- **Google Places API** - Official business data

## Features

### Core Features
- ✅ Business discovery by category and location
- ✅ Configurable search radius
- ✅ Multi-provider support (Apify, Outscraper, Google Places)
- ✅ Website enrichment and contact extraction
- ✅ Email discovery and extraction
- ✅ Phone number extraction and normalization
- ✅ Social profile discovery (Instagram, LinkedIn, Facebook, X)
- ✅ Duplicate detection and deduplication
- ✅ Background job processing
- ✅ Job status tracking and progress monitoring
- ✅ Source evidence tracking
- ✅ CSV export functionality

### Security & Compliance
- ✅ SSRF protection
- ✅ Rate limiting and timeout controls
- ✅ robots.txt respect
- ✅ No authentication bypassing
- ✅ Environment-based configuration
- ✅ API key security

## Project Structure

```
MVP/
├── backend/
│   ├── alembic/                  # Database migrations
│   ├── app/
│   │   ├── api/                  # API routes
│   │   │   └── v1/
│   │   │       ├── discovery.py  # Discovery endpoints
│   │   │       ├── leads.py      # Lead management
│   │   │       ├── health.py     # Health checks
│   │   │       └── stats.py      # Statistics
│   │   ├── core/                 # Core configuration
│   │   │   ├── config.py         # Settings
│   │   │   ├── database.py       # DB setup
│   │   │   └── security.py       # Security utilities
│   │   ├── models/               # SQLAlchemy models
│   │   ├── schemas/              # Pydantic schemas
│   │   ├── providers/            # Provider integrations
│   │   │   ├── discovery/        # Business discovery
│   │   │   ├── enrichment/       # Website enrichment
│   │   │   └── search/           # Web search
│   │   ├── extractors/           # Data extractors
│   │   │   ├── email.py
│   │   │   ├── phone.py
│   │   │   └── social.py
│   │   ├── services/             # Business logic
│   │   └── workers/              # Celery workers
│   ├── tests/                    # Test suite
│   ├── requirements.txt
│   └── main.py                   # FastAPI application
├── frontend/
│   ├── src/
│   │   ├── components/           # React components
│   │   ├── pages/                # Page components
│   │   ├── services/             # API clients
│   │   ├── types/                # TypeScript types
│   │   └── App.tsx
│   ├── package.json
│   └── vite.config.ts
├── docker-compose.yml
├── .env.example
└── SETUP.md
```

## Quick Start

See [SETUP.md](./SETUP.md) for detailed setup instructions.

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- Redis 7+
- Git

### Environment Setup

1. Copy environment file:
```bash
copy .env.example .env
```

2. Configure your API keys in `.env`

3. Start services:
```bash
docker-compose up -d
```

4. Run backend:
```bash
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
python main.py
```

5. Run frontend:
```bash
cd frontend
npm install
npm run dev
```

## API Documentation

Interactive API documentation available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

See [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) for detailed endpoint information.

## Provider Setup

See [PROVIDER_SETUP.md](./PROVIDER_SETUP.md) for:
- How to get API keys
- Provider configuration
- Cost considerations
- Rate limits and quotas

## Architecture

See [ARCHITECTURE.md](./ARCHITECTURE.md) for:
- System design
- Data flow
- Provider architecture
- Security considerations
- Scaling guidelines

## Testing

```bash
cd backend
pytest tests/ -v
```

For integration tests with real providers:
```bash
pytest tests/integration/ -v --real-api
```

## Contributing

1. Follow the existing code structure
2. Add tests for new features
3. Update documentation
4. Ensure all tests pass
5. Follow security guidelines

## License

MIT License - See LICENSE file for details

## Support

For issues and questions, please open an issue on GitHub.

## Disclaimer

This tool is designed for legitimate business research and lead generation purposes only. Users must:
- Comply with all applicable laws and regulations
- Respect website terms of service
- Follow data protection regulations (GDPR, CCPA, etc.)
- Obtain proper consent before contacting discovered leads
- Not use for spam or unauthorized marketing

The platform collects only publicly available business information and respects robots.txt and rate limits.
