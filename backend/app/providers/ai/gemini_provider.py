"""Google Gemini AI Provider implementation."""

import json
import logging
from typing import Dict, Any, List, Optional
import httpx

from app.core.config import settings
from app.providers.ai.base import BaseAIProvider
from app.services.provider_health_service import ProviderHealthService, IntegrationStatus

logger = logging.getLogger(__name__)


class GeminiAIProvider(BaseAIProvider):
    """Google Gemini Flash implementation using official REST API."""

    provider_name: str = "gemini"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = "gemini-1.5-flash"
        self.embedding_model = "text-embedding-004"

    def is_available(self) -> bool:
        return bool(self.api_key and not self.api_key.startswith("sk-or-"))

    async def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ) -> Optional[str]:
        if not self.is_available():
            return None

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        payload: Dict[str, Any] = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

        try:
            async with httpx.AsyncClient(timeout=25.0) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates and "content" in candidates[0]:
                        parts = candidates[0]["content"].get("parts", [])
                        if parts:
                            ProviderHealthService.record_success(self.provider_name)
                            return parts[0].get("text", "")
                elif resp.status_code == 429:
                    ProviderHealthService.record_failure(self.provider_name, "Rate limit reached", IntegrationStatus.RATE_LIMITED)
                elif resp.status_code in [400, 401, 403]:
                    ProviderHealthService.record_failure(self.provider_name, f"Auth failed ({resp.status_code})", IntegrationStatus.INVALID_CREDENTIALS)
                else:
                    ProviderHealthService.record_failure(self.provider_name, f"HTTP {resp.status_code}")
        except Exception as e:
            logger.warning(f"Gemini generate_text error: {e}")
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

        full_prompt = (
            f"{prompt}\n\n"
            f"You MUST format your entire response as a valid JSON object matching this schema description:\n"
            f"{schema_description}\n"
            f"Do not include markdown code block wrappers like ```json if possible, return raw parseable JSON."
        )

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        payload: Dict[str, Any] = {
            "contents": [{"parts": [{"text": full_prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "responseMimeType": "application/json",
            },
        }
        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates and "content" in candidates[0]:
                        parts = candidates[0]["content"].get("parts", [])
                        if parts:
                            text_val = parts[0].get("text", "").strip()
                            if text_val.startswith("```json"):
                                text_val = text_val[7:]
                            if text_val.endswith("```"):
                                text_val = text_val[:-3]
                            ProviderHealthService.record_success(self.provider_name)
                            return json.loads(text_val.strip())
                elif resp.status_code == 429:
                    ProviderHealthService.record_failure(self.provider_name, "Rate limit reached", IntegrationStatus.RATE_LIMITED)
                else:
                    ProviderHealthService.record_failure(self.provider_name, f"HTTP {resp.status_code}")
        except Exception as e:
            logger.warning(f"Gemini generate_structured error: {e}")
            ProviderHealthService.record_failure(self.provider_name, str(e))
        return None

    async def generate_embeddings(self, text: str) -> Optional[List[float]]:
        if not self.is_available():
            return None

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.embedding_model}:embedContent?key={self.api_key}"
        payload = {
            "model": f"models/{self.embedding_model}",
            "content": {"parts": [{"text": text[:3000]}]},
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    values = data.get("embedding", {}).get("values")
                    if values:
                        return values
        except Exception as e:
            logger.warning(f"Gemini generate_embeddings error: {e}")
        return None

