"""Application configuration using Pydantic settings."""

from typing import List, Optional, Union
from pydantic import Field, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
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

    # Redis
    REDIS_URL: Union[RedisDsn, str] = Field(default="redis://localhost:6379/0")

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
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

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
    # Instagram Content Publishing API
    INSTAGRAM_ACCESS_TOKEN: Optional[str] = None
    INSTAGRAM_BUSINESS_ACCOUNT_ID: Optional[str] = None

    # Facebook Pages Graph API
    FACEBOOK_PAGE_ACCESS_TOKEN: Optional[str] = None
    FACEBOOK_PAGE_ID: Optional[str] = None

    # X (Twitter) API v2
    TWITTER_API_KEY: Optional[str] = None
    TWITTER_API_SECRET: Optional[str] = None
    TWITTER_ACCESS_TOKEN: Optional[str] = None
    TWITTER_ACCESS_TOKEN_SECRET: Optional[str] = None
    TWITTER_BEARER_TOKEN: Optional[str] = None

    # LinkedIn Posts API v2 (Personal & Organization Pages)
    LINKEDIN_CLIENT_ID: Optional[str] = None
    LINKEDIN_CLIENT_SECRET: Optional[str] = None
    LINKEDIN_ACCESS_TOKEN: Optional[str] = None
    LINKEDIN_PERSON_URN: Optional[str] = None  # e.g. "urn:li:person:abcdef"
    LINKEDIN_ORGANIZATION_URN: Optional[str] = None  # e.g. "urn:li:organization:123456"

    # Lead Qualification Weights (Default 25/25/20/15/15)
    ICP_WEIGHT_FIT: float = 0.25
    ICP_WEIGHT_PAIN: float = 0.25
    ICP_WEIGHT_TIMING: float = 0.20
    ICP_WEIGHT_REACHABILITY: float = 0.15
    ICP_WEIGHT_EVIDENCE: float = 0.15

    # Security & Auth
    SECRET_KEY: str = "development-secret-key-change-in-production-ai-sales-crm-os"
    ADMIN_API_KEY: str = "dev-admin-key-ai-sales-crm"
    AUTH_ENABLED: bool = False
    ALLOWED_ORIGINS: List[str] = Field(
        default=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
        ]
    )

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_BURST: int = 10

    # Job Configuration
    MAX_RESULTS_PER_JOB: int = 500
    DEFAULT_SEARCH_RADIUS_KM: int = 10
    JOB_TIMEOUT_SECONDS: int = 3600

    # Crawler Configuration
    MAX_CONCURRENT_REQUESTS: int = 5
    REQUEST_DELAY_SECONDS: int = 1
    MAX_RETRIES: int = 3
    USER_AGENT: str = "CRM-Lead-Discovery-Bot/1.0"

    # SSRF Protection
    ALLOW_PRIVATE_IPS: bool = False
    BLOCKED_DOMAINS: List[str] = Field(
        default=["localhost", "127.0.0.1", "0.0.0.0"]
    )

    @field_validator("BLOCKED_DOMAINS", mode="before")
    @classmethod
    def parse_blocked_domains(cls, v):
        if isinstance(v, str):
            return [domain.strip() for domain in v.split(",")]
        return v

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"


# Global settings instance
settings = Settings()
