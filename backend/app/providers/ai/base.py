"""Abstract Base Class for AI and Reasoning Providers."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


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
