"""AI Provider Router with Automatic Fallback Chain."""

import logging
from typing import Dict, Any, List, Optional

from app.core.config import settings
from app.providers.ai.base import BaseAIProvider
from app.providers.ai.gemini_provider import GeminiAIProvider
from app.providers.ai.openrouter_provider import OpenRouterAIProvider
from app.providers.ai.heuristic_provider import HeuristicAIProvider

logger = logging.getLogger(__name__)


class AIProviderRouter:
    """
    Intelligent router coordinating AI execution across Gemini, OpenRouter,
    and Heuristic providers. Automatically falls back without throwing unhandled exceptions.
    """

    def __init__(self):
        self.gemini = GeminiAIProvider()
        self.openrouter = OpenRouterAIProvider()
        self.heuristic = HeuristicAIProvider()

    def get_preferred_provider(self, custom_key: Optional[str] = None) -> BaseAIProvider:
        """Select highest priority configured provider."""
        if custom_key:
            if custom_key.startswith("sk-or-"):
                return OpenRouterAIProvider(api_key=custom_key)
            return GeminiAIProvider(api_key=custom_key)

        if settings.DEFAULT_AI_PROVIDER == "openrouter" and self.openrouter.is_available():
            return self.openrouter
        if self.gemini.is_available():
            return self.gemini
        if self.openrouter.is_available():
            return self.openrouter
        return self.heuristic

    async def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        custom_key: Optional[str] = None,
        temperature: float = 0.3,
    ) -> str:
        """Attempt text generation with fallback chain."""
        providers = []
        if custom_key:
            providers.append(self.get_preferred_provider(custom_key))
        else:
            if self.gemini.is_available():
                providers.append(self.gemini)
            if self.openrouter.is_available():
                providers.append(self.openrouter)
        providers.append(self.heuristic)

        for p in providers:
            try:
                res = await p.generate_text(prompt, system_instruction=system_instruction, temperature=temperature)
                if res:
                    return res
            except Exception as e:
                logger.warning(f"Provider {p.provider_name} failed in text chain: {e}")

        # Final guarantee
        return await self.heuristic.generate_text(prompt)

    async def generate_structured(
        self,
        prompt: str,
        schema_description: str,
        system_instruction: Optional[str] = None,
        custom_key: Optional[str] = None,
        temperature: float = 0.2,
    ) -> Dict[str, Any]:
        """Attempt structured generation with fallback chain."""
        providers = []
        if custom_key:
            providers.append(self.get_preferred_provider(custom_key))
        else:
            if self.gemini.is_available():
                providers.append(self.gemini)
            if self.openrouter.is_available():
                providers.append(self.openrouter)
        providers.append(self.heuristic)

        for p in providers:
            try:
                res = await p.generate_structured(
                    prompt=prompt,
                    schema_description=schema_description,
                    system_instruction=system_instruction,
                    temperature=temperature,
                )
                if res and isinstance(res, dict):
                    return res
            except Exception as e:
                logger.warning(f"Provider {p.provider_name} failed in structured chain: {e}")

        # Final guarantee
        res = await self.heuristic.generate_structured(prompt, schema_description)
        return res or {}

    async def generate_embeddings(self, text: str) -> List[float]:
        """Attempt vector embedding generation with fallback to heuristic hash vector."""
        if self.gemini.is_available():
            try:
                emb = await self.gemini.generate_embeddings(text)
                if emb:
                    return emb
            except Exception as e:
                logger.warning(f"Gemini embeddings failed: {e}")

        # Fallback to deterministic heuristic vector
        return await self.heuristic.generate_embeddings(text) or [0.0] * 128


# Global router singleton
ai_router = AIProviderRouter()

