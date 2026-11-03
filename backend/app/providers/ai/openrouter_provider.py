"""OpenRouter AI Provider implementation."""

import json
import logging
from typing import Dict, Any, List, Optional
import httpx

from app.core.config import settings
from app.providers.ai.base import BaseAIProvider
from app.services.provider_health_service import ProviderHealthService, IntegrationStatus

logger = logging.getLogger(__name__)


class OpenRouterAIProvider(BaseAIProvider):
    """OpenRouter multi-model completion API provider."""

    provider_name: str = "openrouter"

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.OPENROUTER_API_KEY
        self.model = model or settings.OPENROUTER_MODEL

    def is_available(self) -> bool:
        return bool(self.api_key)

    async def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ) -> Optional[str]:
        if not self.is_available():
            return None

        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": settings.FRONTEND_URL,
            "X-Title": settings.APP_NAME,
        }
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    choices = data.get("choices", [])
                    if choices:
                        ProviderHealthService.record_success(self.provider_name)
                        return choices[0].get("message", {}).get("content", "")
                elif resp.status_code == 429:
                    ProviderHealthService.record_failure(self.provider_name, "Rate limited", IntegrationStatus.RATE_LIMITED)
                elif resp.status_code in [401, 403]:
                    ProviderHealthService.record_failure(self.provider_name, "Auth failed", IntegrationStatus.INVALID_CREDENTIALS)
                else:
                    ProviderHealthService.record_failure(self.provider_name, f"HTTP {resp.status_code}")
        except Exception as e:
            logger.warning(f"OpenRouter generate_text error: {e}")
            ProviderHealthService.record_failure(self.provider_name, str(e))
        return None

    async def generate_structured(
        self,
        prompt: str,
        schema_description: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
    ) -> Optional[Dict[str, Any]]:
        if not self.is_available():
            return None

        combined_prompt = (
            f"{prompt}\n\n"
            f"You MUST output ONLY a valid JSON object matching this schema description:\n"
            f"{schema_description}\n"
            f"Do not include any other markdown or conversational filler."
        )

        text_out = await self.generate_text(
            prompt=combined_prompt,
            system_instruction=system_instruction or "You are a structured data extractor that returns only valid JSON.",
            temperature=temperature,
        )

        if text_out:
            clean = text_out.strip()
            if clean.startswith("```json"):
                clean = clean[7:]
            if clean.endswith("```"):
                clean = clean[:-3]
            try:
                return json.loads(clean.strip())
            except Exception as e:
                logger.warning(f"Failed to parse JSON from OpenRouter output: {e}")
        return None

    async def generate_embeddings(self, text: str) -> Optional[List[float]]:
        # OpenRouter focus is chat completion; return None so router falls back gracefully
        return None
