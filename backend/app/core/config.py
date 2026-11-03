"""Application configuration using Pydantic settings."""

from typing import List, Optional
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
    APP_NAME: str = "CRM Lead Discovery"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # Server
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:5173"

    # Database
    DATABASE_URL: PostgresDsn = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/crm_leads"
    )
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    # Redis
    REDIS_URL: RedisDsn = Field(default="redis://localhost:6379/0")

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # Provider API Keys
    APIFY_API_TOKEN: Optional[str] = None
    APIFY_MAPS_ACTOR_ID: str = "nwua9Gu5YrADL7ZDj"
    APIFY_REQUEST_TIMEOUT: int = 300

    OUTSCRAPER_API_KEY: Optional[str] = None
    OUTSCRAPER_REQUEST_TIMEOUT: int = 300

    GOOGLE_PLACES_API_KEY: Optional[str] = None
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

    # Security
    SECRET_KEY: str = "change-this-secret-key-in-production"
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
