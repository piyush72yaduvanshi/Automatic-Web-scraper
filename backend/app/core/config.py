"""Application configuration using Pydantic settings."""

from pathlib import Path
import os
from typing import List, Optional, Union
from dotenv import load_dotenv
from pydantic import Field, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Proactively discover and load .env files from both backend/ and project root
_CURRENT_FILE = Path(__file__).resolve()
_BACKEND_DIR = _CURRENT_FILE.parent.parent.parent  # d:\MVP\backend
_ROOT_DIR = _BACKEND_DIR.parent  # d:\MVP

_CANDIDATE_ENVS = [
    _BACKEND_DIR / ".env",
    _ROOT_DIR / ".env",
    Path(".env"),
    Path("backend/.env"),
]

for _env_path in _CANDIDATE_ENVS:
    if _env_path.is_file():
        load_dotenv(dotenv_path=_env_path, override=False)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=tuple(str(p) for p in _CANDIDATE_ENVS if p.is_file()) or ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Application
    APP_NAME: str = "AI Sales & CRM Operating System"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # Server
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:5173"

    # Database (Dialect-agnostic: supports postgresql+psycopg, postgresql+asyncpg, sqlite)
    DATABASE_URL: Union[PostgresDsn, str] = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/crm_leads"
    )
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_POOL_RECYCLE: int = 3600

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_database_url(cls, v):
        if not v:
            return "postgresql+psycopg://postgres:postgres@localhost:5432/crm_leads"
        return str(v)

    # Redis
    REDIS_URL: Union[RedisDsn, str] = Field(
        default="redis://:redis_dev_password_change_in_prod@localhost:6379/0"
    )
    REDIS_PASSWORD: Optional[str] = "redis_dev_password_change_in_prod"

    @field_validator("REDIS_URL", mode="before")
    @classmethod
    def assemble_redis_url(cls, v):
        if not v:
            return "redis://:redis_dev_password_change_in_prod@localhost:6379/0"
        s = str(v)
        # If localhost Redis without password, inject container dev password
        if "localhost:6379" in s and "@" not in s:
            pwd = os.getenv("REDIS_PASSWORD", "redis_dev_password_change_in_prod")
            return f"redis://:{pwd}@localhost:6379/0"
        return s

    # MinIO Object Storage (Images, Creatives, Lead Collateral & Export Storage)
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET_NAME: str = "crm-assets"
    MINIO_SECURE: bool = False
    MINIO_PUBLIC_URL: Optional[str] = "http://localhost:9000"

    # pgvector Vector Database
    PGVECTOR_ENABLED: bool = True
    VECTOR_DIMENSION: int = 768

    # Celery
    CELERY_BROKER_URL: str = "redis://:redis_dev_password_change_in_prod@localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://:redis_dev_password_change_in_prod@localhost:6379/0"

    @field_validator("CELERY_BROKER_URL", "CELERY_RESULT_BACKEND", mode="before")
    @classmethod
    def assemble_celery_url(cls, v):
        if not v:
            return "redis://:redis_dev_password_change_in_prod@localhost:6379/0"
        s = str(v)
        if "localhost:6379" in s and "@" not in s:
            pwd = os.getenv("REDIS_PASSWORD", "redis_dev_password_change_in_prod")
            return f"redis://:{pwd}@localhost:6379/0"
        return s

    # Provider API Keys
    APIFY_API_TOKEN: Optional[str] = None
    APIFY_MAPS_ACTOR_ID: str = "nwua9Gu5YrADL7ZDj"
    APIFY_REQUEST_TIMEOUT: int = 300

    OUTSCRAPER_API_KEY: Optional[str] = None
    OUTSCRAPER_REQUEST_TIMEOUT: int = 300

    # Official Google Maps Platform / Places API
    GOOGLE_PLACES_API_KEY: Optional[str] = None
    GOOGLE_MAPS_API_KEY: Optional[str] = None
    GOOGLE_PLACES_REQUEST_TIMEOUT: int = 30

    FIRECRAWL_API_KEY: Optional[str] = None
    FIRECRAWL_REQUEST_TIMEOUT: int = 60
    FIRECRAWL_MAX_PAGES: int = 5

    SEARCH_API_PROVIDER: str = "serpapi"
    SEARCH_API_KEY: Optional[str] = None
    SERPAPI_API_KEY: Optional[str] = None
    SEARCH_API_TIMEOUT: int = 30

    # AI Intelligence Providers (Gemini / OpenRouter)
    GEMINI_API_KEY: Optional[str] = None
    OPENROUTER_API_KEY: Optional[str] = None
    OPENROUTER_MODEL: str = "google/gemini-2.0-flash-001"
    DEFAULT_AI_PROVIDER: str = "gemini"
    EMBEDDING_PROVIDER: str = "gemini"

    # Communication Providers: Email (Gmail) & WhatsApp
    GMAIL_CLIENT_ID: Optional[str] = None
    GMAIL_CLIENT_SECRET: Optional[str] = None
    GMAIL_REFRESH_TOKEN: Optional[str] = None
    GMAIL_REDIRECT_URI: str = "http://localhost:8000/api/v1/integrations/gmail/callback"
    GMAIL_SENDER_EMAIL: Optional[str] = None

    WHATSAPP_PHONE_NUMBER_ID: Optional[str] = None
    WHATSAPP_ACCESS_TOKEN: Optional[str] = None
    WHATSAPP_VERIFY_TOKEN: str = "crm_whatsapp_verify_token_default"
    WHATSAPP_BUSINESS_ACCOUNT_ID: Optional[str] = None

    # Social Media Automation Providers (Official APIs)
    INSTAGRAM_ACCESS_TOKEN: Optional[str] = None
    INSTAGRAM_BUSINESS_ACCOUNT_ID: Optional[str] = None
    FACEBOOK_PAGE_ACCESS_TOKEN: Optional[str] = None
    FACEBOOK_PAGE_ID: Optional[str] = None
    TWITTER_BEARER_TOKEN: Optional[str] = None
    TWITTER_API_KEY: Optional[str] = None
    TWITTER_API_SECRET: Optional[str] = None
    TWITTER_ACCESS_TOKEN: Optional[str] = None
    TWITTER_ACCESS_TOKEN_SECRET: Optional[str] = None
    LINKEDIN_CLIENT_ID: Optional[str] = None
    LINKEDIN_CLIENT_SECRET: Optional[str] = None
    LINKEDIN_ACCESS_TOKEN: Optional[str] = None
    LINKEDIN_ORG_ID: Optional[str] = None
    LINKEDIN_PERSON_URN: Optional[str] = None
    LINKEDIN_ORGANIZATION_URN: Optional[str] = None

    # Security
    SECRET_KEY: str = "development-secret-key-change-in-production"
    API_KEY: Optional[str] = None
    AUTH_ENABLED: bool = False
    ADMIN_API_KEY: str = "dev-admin-api-key"
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:5173", "http://localhost:3000"]
    )

    # AI Lead Qualification ICP Weights
    ICP_WEIGHT_FIT: float = 0.25
    ICP_WEIGHT_PAIN: float = 0.25
    ICP_WEIGHT_TIMING: float = 0.20
    ICP_WEIGHT_REACHABILITY: float = 0.15
    ICP_WEIGHT_EVIDENCE: float = 0.15

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_BURST: int = 10
    RATE_LIMIT_DISCOVERY: str = "10/minute"
    RATE_LIMIT_AI_AGENTS: str = "20/minute"
    RATE_LIMIT_OUTREACH: str = "10/minute"
    RATE_LIMIT_DEFAULT: str = "60/minute"

    # Job Configuration
    MAX_RESULTS_PER_JOB: int = 500
    DEFAULT_SEARCH_RADIUS_KM: int = 10
    JOB_TIMEOUT_SECONDS: int = 3600

    # Crawler Configuration
    MAX_CONCURRENT_REQUESTS: int = 5
    REQUEST_DELAY_SECONDS: float = 1.0
    MAX_RETRIES: int = 3
    USER_AGENT: str = "CRM-Lead-Discovery-Bot/1.0"

    # SSRF Protection
    ALLOW_PRIVATE_IPS: bool = False
    BLOCKED_DOMAINS: List[str] = Field(
        default=["localhost", "127.0.0.1", "0.0.0.0"]
    )

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_and_validate_origins(cls, v):
        """Parse and validate ALLOWED_ORIGINS with production wildcard protection."""
        if isinstance(v, str):
            import json
            try:
                origins = json.loads(v)
            except Exception:
                origins = [i.strip() for i in v.split(",") if i.strip()]
        else:
            origins = v
        
        # In production, reject wildcard patterns in origins
        import os
        if os.getenv("APP_ENV") == "production":
            for origin in origins:
                if "*" in origin and origin != "*":
                    raise ValueError(f"Wildcard origins not allowed in production: {origin}")
        
        return origins

    @field_validator("BLOCKED_DOMAINS", mode="before")
    @classmethod
    def parse_str_list(cls, v):
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except Exception:
                return [i.strip() for i in v.split(",") if i.strip()]
        return v


settings = Settings()
