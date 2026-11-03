"""Centralized Provider Configuration and Health Management Service.

Provides fault tolerance, credential inspection, status tracking, and graceful fallback
without crashing when API keys are absent, expired, or rate-limited.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import httpx
from sqlalchemy import text

from app.core.config import settings

logger = logging.getLogger(__name__)


class IntegrationStatus(str, Enum):
    CONFIGURED = "CONFIGURED"
    NOT_CONFIGURED = "NOT_CONFIGURED"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    EXPIRED = "EXPIRED"
    RATE_LIMITED = "RATE_LIMITED"
    TEMPORARILY_UNAVAILABLE = "TEMPORARILY_UNAVAILABLE"
    DISABLED = "DISABLED"
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"


class IntegrationCategory(str, Enum):
    AI = "AI & Reasoning"
    DISCOVERY = "Lead Discovery"
    ENRICHMENT = "Web Enrichment"
    COMMUNICATION = "Outreach & Messaging"
    INFRASTRUCTURE = "Core Infrastructure"


class ProviderHealthService:
    """Manages runtime status and health verification for all external integrations."""

    # In-memory runtime state for providers
    _runtime_state: Dict[str, Dict[str, Any]] = {}
    _disabled_providers: set = set()

    @classmethod
    def _init_provider(cls, name: str, display_name: str, category: IntegrationCategory, description: str):
        if name not in cls._runtime_state:
            cls._runtime_state[name] = {
                "name": name,
                "display_name": display_name,
                "category": category.value,
                "description": description,
                "status": IntegrationStatus.NOT_CONFIGURED.value,
                "is_configured": False,
                "is_enabled": True,
                "last_checked_at": None,
                "last_success_at": None,
                "last_error": None,
                "user_message": "",
            }

    @classmethod
    def record_success(cls, provider_name: str):
        """Mark a provider execution as successful."""
        if provider_name in cls._runtime_state:
            cls._runtime_state[provider_name]["status"] = IntegrationStatus.HEALTHY.value
            cls._runtime_state[provider_name]["last_success_at"] = datetime.utcnow().isoformat()
            cls._runtime_state[provider_name]["last_error"] = None

    @classmethod
    def record_failure(cls, provider_name: str, error: str, status: IntegrationStatus = IntegrationStatus.TEMPORARILY_UNAVAILABLE):
        """Mark a provider execution as degraded/failed with a safe error message."""
        if provider_name in cls._runtime_state:
            cls._runtime_state[provider_name]["status"] = status.value
            # Sanitize error to avoid leaking API keys
            safe_error = str(error).replace(settings.SECRET_KEY, "***")
            if settings.GEMINI_API_KEY:
                safe_error = safe_error.replace(settings.GEMINI_API_KEY, "***")
            if settings.OPENROUTER_API_KEY:
                safe_error = safe_error.replace(settings.OPENROUTER_API_KEY, "***")
            cls._runtime_state[provider_name]["last_error"] = safe_error[:300]

    @classmethod
    def toggle_provider(cls, provider_name: str, enabled: bool) -> bool:
        """Enable or disable a specific provider."""
        if provider_name in cls._runtime_state:
            cls._runtime_state[provider_name]["is_enabled"] = enabled
            if not enabled:
                cls._runtime_state[provider_name]["status"] = IntegrationStatus.DISABLED.value
                cls._disabled_providers.add(provider_name)
            else:
                cls._disabled_providers.discard(provider_name)
            return True
        return False

    @classmethod
    def get_all_statuses(cls, db_session=None) -> List[Dict[str, Any]]:
        """Return fresh statuses of all system integrations."""
        # Ensure definitions exist
        cls._init_provider("gemini", "Google Gemini API", IntegrationCategory.AI, "Primary LLM for company research, lead scoring, and outreach drafting.")
        cls._init_provider("openrouter", "OpenRouter AI", IntegrationCategory.AI, "Secondary / Fallback multi-model LLM router.")
        cls._init_provider("heuristic_nlp", "Heuristic NLP Engine", IntegrationCategory.AI, "Built-in offline regex & rule-based analyzer (zero external dependencies).")
        cls._init_provider("serpapi", "SerpAPI Search Engine", IntegrationCategory.DISCOVERY, "Google Maps & Google Search automated scraping API.")
        cls._init_provider("apify", "Apify Actor Platform", IntegrationCategory.DISCOVERY, "Cloud web scrapers and Google Maps business crawlers.")
        cls._init_provider("firecrawl", "Firecrawl Web Crawler", IntegrationCategory.ENRICHMENT, "Deep website crawling and markdown/JSON-LD content extraction.")
        cls._init_provider("gmail", "Gmail / Google Workspace", IntegrationCategory.COMMUNICATION, "Official Gmail OAuth API for inbox sync, threads, and approved emails.")
        cls._init_provider("whatsapp", "WhatsApp Business Cloud API", IntegrationCategory.COMMUNICATION, "Meta WhatsApp Business Platform API for customer messaging.")
        cls._init_provider("database", "Primary Database", IntegrationCategory.INFRASTRUCTURE, "PostgreSQL or SQLite storage for leads, CRM, campaigns, and memory.")
        cls._init_provider("redis", "Redis Cache & Broker", IntegrationCategory.INFRASTRUCTURE, "High-speed caching and Celery task queue broker.")
        cls._init_provider("celery", "Celery Background Worker", IntegrationCategory.INFRASTRUCTURE, "Distributed asynchronous task execution for bulk discovery & research.")

        # 1. Heuristic NLP is always healthy and active
        cls._runtime_state["heuristic_nlp"]["is_configured"] = True
        cls._runtime_state["heuristic_nlp"]["status"] = IntegrationStatus.HEALTHY.value
        cls._runtime_state["heuristic_nlp"]["user_message"] = "Built-in algorithmic NLP engine is always available offline."

        # 2. Gemini status
        gemini_key = settings.GEMINI_API_KEY
        if not gemini_key and not cls._runtime_state["gemini"].get("last_success_at"):
            cls._runtime_state["gemini"]["is_configured"] = False
            cls._runtime_state["gemini"]["status"] = IntegrationStatus.NOT_CONFIGURED.value
            cls._runtime_state["gemini"]["user_message"] = "Gemini API key is not configured. Heuristic NLP will be used for synthesis."
        else:
            cls._runtime_state["gemini"]["is_configured"] = True
            if cls._runtime_state["gemini"]["status"] not in [IntegrationStatus.DISABLED.value, IntegrationStatus.INVALID_CREDENTIALS.value]:
                cls._runtime_state["gemini"]["status"] = IntegrationStatus.HEALTHY.value
                cls._runtime_state["gemini"]["user_message"] = "Gemini API key configured and ready."


        # 3. OpenRouter status
        openrouter_key = settings.OPENROUTER_API_KEY
        if not openrouter_key:
            cls._runtime_state["openrouter"]["is_configured"] = False
            cls._runtime_state["openrouter"]["status"] = IntegrationStatus.NOT_CONFIGURED.value
            cls._runtime_state["openrouter"]["user_message"] = "OpenRouter API key is not configured."
        else:
            cls._runtime_state["openrouter"]["is_configured"] = True
            if cls._runtime_state["openrouter"]["status"] != IntegrationStatus.DISABLED.value:
                cls._runtime_state["openrouter"]["status"] = IntegrationStatus.HEALTHY.value
                cls._runtime_state["openrouter"]["user_message"] = f"OpenRouter configured using model {settings.OPENROUTER_MODEL}."

        # 4. SerpAPI status
        search_key = settings.SEARCH_API_KEY or settings.SERPAPI_API_KEY
        if not search_key:
            cls._runtime_state["serpapi"]["is_configured"] = False
            cls._runtime_state["serpapi"]["status"] = IntegrationStatus.NOT_CONFIGURED.value
            cls._runtime_state["serpapi"]["user_message"] = "SerpAPI key not configured. Direct web scraping and user CSV import remain active."
        else:
            cls._runtime_state["serpapi"]["is_configured"] = True
            cls._runtime_state["serpapi"]["status"] = IntegrationStatus.HEALTHY.value
            cls._runtime_state["serpapi"]["user_message"] = "SerpAPI configured for Google Maps and Web search."

        # 5. Apify status
        if not settings.APIFY_API_TOKEN:
            cls._runtime_state["apify"]["is_configured"] = False
            cls._runtime_state["apify"]["status"] = IntegrationStatus.NOT_CONFIGURED.value
            cls._runtime_state["apify"]["user_message"] = "Apify token not configured."
        else:
            cls._runtime_state["apify"]["is_configured"] = True
            cls._runtime_state["apify"]["status"] = IntegrationStatus.HEALTHY.value
            cls._runtime_state["apify"]["user_message"] = "Apify integration configured."

        # 6. Firecrawl status
        if not settings.FIRECRAWL_API_KEY:
            cls._runtime_state["firecrawl"]["is_configured"] = False
            cls._runtime_state["firecrawl"]["status"] = IntegrationStatus.NOT_CONFIGURED.value
            cls._runtime_state["firecrawl"]["user_message"] = "Firecrawl key not configured. Direct HTTP scraping fallback will be used."
        else:
            cls._runtime_state["firecrawl"]["is_configured"] = True
            cls._runtime_state["firecrawl"]["status"] = IntegrationStatus.HEALTHY.value
            cls._runtime_state["firecrawl"]["user_message"] = "Firecrawl configured for deep website analysis."

        # 7. Gmail status
        has_gmail = bool(settings.GMAIL_CLIENT_ID and (settings.GMAIL_REFRESH_TOKEN or settings.GMAIL_CLIENT_SECRET))
        if not has_gmail:
            cls._runtime_state["gmail"]["is_configured"] = False
            cls._runtime_state["gmail"]["status"] = IntegrationStatus.NOT_CONFIGURED.value
            cls._runtime_state["gmail"]["user_message"] = "Gmail OAuth not configured. Email drafts can be generated but live sending is disabled."
        else:
            cls._runtime_state["gmail"]["is_configured"] = True
            cls._runtime_state["gmail"]["status"] = IntegrationStatus.HEALTHY.value
            cls._runtime_state["gmail"]["user_message"] = "Gmail OAuth integration configured for inbox sync and outreach."

        # 8. WhatsApp status
        has_whatsapp = bool(settings.WHATSAPP_ACCESS_TOKEN and settings.WHATSAPP_PHONE_NUMBER_ID)
        if not has_whatsapp:
            cls._runtime_state["whatsapp"]["is_configured"] = False
            cls._runtime_state["whatsapp"]["status"] = IntegrationStatus.NOT_CONFIGURED.value
            cls._runtime_state["whatsapp"]["user_message"] = "WhatsApp Business API not configured. WhatsApp module remains safely disabled."
        else:
            cls._runtime_state["whatsapp"]["is_configured"] = True
            cls._runtime_state["whatsapp"]["status"] = IntegrationStatus.HEALTHY.value
            cls._runtime_state["whatsapp"]["user_message"] = "WhatsApp Cloud API integration configured."

        # 9. Database check
        if db_session:
            try:
                db_session.execute(text("SELECT 1"))
                cls._runtime_state["database"]["is_configured"] = True
                cls._runtime_state["database"]["status"] = IntegrationStatus.HEALTHY.value
                cls._runtime_state["database"]["user_message"] = "Database connection operational."
            except Exception as e:
                cls._runtime_state["database"]["status"] = IntegrationStatus.DEGRADED.value
                cls._runtime_state["database"]["user_message"] = f"Database connection warning: {str(e)[:100]}"
        else:
            cls._runtime_state["database"]["is_configured"] = True
            cls._runtime_state["database"]["status"] = IntegrationStatus.HEALTHY.value
            cls._runtime_state["database"]["user_message"] = "Database ready."

        # 10. Redis check
        try:
            import redis
            r = redis.from_url(str(settings.REDIS_URL), socket_timeout=1.0)
            r.ping()
            cls._runtime_state["redis"]["is_configured"] = True
            cls._runtime_state["redis"]["status"] = IntegrationStatus.HEALTHY.value
            cls._runtime_state["redis"]["user_message"] = "Redis cache and broker operational."
        except Exception:
            cls._runtime_state["redis"]["is_configured"] = False
            cls._runtime_state["redis"]["status"] = IntegrationStatus.TEMPORARILY_UNAVAILABLE.value
            cls._runtime_state["redis"]["user_message"] = "Redis unavailable. Synchronous background tasks active as fallback."

        # 11. Celery check
        if cls._runtime_state["redis"]["status"] == IntegrationStatus.HEALTHY.value:
            cls._runtime_state["celery"]["is_configured"] = True
            cls._runtime_state["celery"]["status"] = IntegrationStatus.HEALTHY.value
            cls._runtime_state["celery"]["user_message"] = "Celery task queue ready."
        else:
            cls._runtime_state["celery"]["is_configured"] = False
            cls._runtime_state["celery"]["status"] = IntegrationStatus.DEGRADED.value
            cls._runtime_state["celery"]["user_message"] = "Celery worker offline. Running in-process background executor."

        # Respect manual disabled flags
        for name in cls._disabled_providers:
            if name in cls._runtime_state:
                cls._runtime_state[name]["status"] = IntegrationStatus.DISABLED.value
                cls._runtime_state[name]["is_enabled"] = False

        for k in cls._runtime_state:
            cls._runtime_state[k]["last_checked_at"] = datetime.utcnow().isoformat()

        return list(cls._runtime_state.values())

    @classmethod
    async def validate_provider(cls, provider_name: str) -> Dict[str, Any]:
        """Test connection/credentials for a specific provider on demand."""
        statuses = {s["name"]: s for s in cls.get_all_statuses()}
        if provider_name not in statuses:
            return {"success": False, "status": IntegrationStatus.NOT_CONFIGURED.value, "message": f"Unknown provider: {provider_name}"}

        provider_info = statuses[provider_name]
        if not provider_info["is_configured"]:
            return {
                "success": False,
                "status": IntegrationStatus.NOT_CONFIGURED.value,
                "message": f"{provider_info['display_name']} credentials are not configured in environment.",
            }

        # Perform live test based on provider
        try:
            if provider_name == "gemini":
                key = settings.GEMINI_API_KEY
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.get(f"https://generativelanguage.googleapis.com/v1beta/models?key={key}")
                    if resp.status_code == 200:
                        cls.record_success("gemini")
                        return {"success": True, "status": IntegrationStatus.HEALTHY.value, "message": "Gemini API authenticated successfully."}
                    else:
                        cls.record_failure("gemini", f"HTTP {resp.status_code}: {resp.text}", IntegrationStatus.INVALID_CREDENTIALS)
                        return {"success": False, "status": IntegrationStatus.INVALID_CREDENTIALS.value, "message": f"Gemini API returned HTTP {resp.status_code}."}

            elif provider_name == "openrouter":
                key = settings.OPENROUTER_API_KEY
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.get("https://openrouter.ai/api/v1/auth/key", headers={"Authorization": f"Bearer {key}"})
                    if resp.status_code == 200:
                        cls.record_success("openrouter")
                        return {"success": True, "status": IntegrationStatus.HEALTHY.value, "message": "OpenRouter API authenticated successfully."}
                    else:
                        cls.record_failure("openrouter", f"HTTP {resp.status_code}: {resp.text}", IntegrationStatus.INVALID_CREDENTIALS)
                        return {"success": False, "status": IntegrationStatus.INVALID_CREDENTIALS.value, "message": f"OpenRouter returned HTTP {resp.status_code}."}

            elif provider_name == "serpapi":
                key = settings.SEARCH_API_KEY or settings.SERPAPI_API_KEY
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.get(f"https://serpapi.com/account?api_key={key}")
                    if resp.status_code == 200:
                        cls.record_success("serpapi")
                        return {"success": True, "status": IntegrationStatus.HEALTHY.value, "message": "SerpAPI authenticated successfully."}
                    else:
                        cls.record_failure("serpapi", f"HTTP {resp.status_code}", IntegrationStatus.INVALID_CREDENTIALS)
                        return {"success": False, "status": IntegrationStatus.INVALID_CREDENTIALS.value, "message": f"SerpAPI returned HTTP {resp.status_code}."}

            elif provider_name == "heuristic_nlp":
                return {"success": True, "status": IntegrationStatus.HEALTHY.value, "message": "Heuristic NLP engine operational."}

            else:
                return {"success": True, "status": provider_info["status"], "message": f"{provider_info['display_name']} configuration verified."}

        except Exception as e:
            cls.record_failure(provider_name, str(e))
            return {"success": False, "status": IntegrationStatus.TEMPORARILY_UNAVAILABLE.value, "message": f"Validation failed: {str(e)[:150]}"}
