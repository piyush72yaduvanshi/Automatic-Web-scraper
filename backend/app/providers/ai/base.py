"""Abstract Base Class for AI and Reasoning Providers."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import json
import re
import logging

logger = logging.getLogger(__name__)


def clean_and_parse_json(raw_text: Optional[str]) -> Optional[Any]:
    """
    Robustly extract and parse JSON from LLM outputs, handling:
    - Pure JSON strings
    - ```json ... ``` markdown fences
    - ``` ... ``` untagged code fences
    - Preamble/postamble conversational text around JSON objects or arrays
    """
    if not raw_text:
        return None

    text = raw_text.strip()

    # 1. Direct attempt
    try:
        return json.loads(text)
    except Exception:
        pass

    # 2. Extract from markdown code fences (```json ... ``` or ``` ... ```)
    code_block_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
    if code_block_match:
        extracted = code_block_match.group(1).strip()
        try:
            return json.loads(extracted)
        except Exception:
            pass

    # 3. Search for outermost JSON object { ... } or array [ ... ]
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace > first_brace:
        try:
            return json.loads(text[first_brace : last_brace + 1])
        except Exception:
            pass

    first_bracket = text.find("[")
    last_bracket = text.rfind("]")
    if first_bracket != -1 and last_bracket > first_bracket:
        try:
            return json.loads(text[first_bracket : last_bracket + 1])
        except Exception:
            pass

    logger.warning(f"Failed to extract valid JSON from LLM response (preview: {text[:150]}...)")
    return None


class BaseAIProvider(ABC):
    """Abstract interface that all AI reasoning and extraction providers must implement."""

    provider_name: str = "base"

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider credentials and configuration are present."""
        pass

    @abstractmethod
    async def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ) -> Optional[str]:
        """Generate unstructured natural language response."""
        pass

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        schema_description: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
    ) -> Optional[Dict[str, Any]]:
        """Generate structured JSON response conforming to requested schema."""
        pass

    @abstractmethod
    async def generate_embeddings(self, text: str) -> Optional[List[float]]:
        """Generate vector embedding for semantic search / RAG."""
        pass
