"""Base AI Provider interface.

All AI providers must implement this interface so the model router
can treat them uniformly. Providers handle prompt formatting,
API calls, and response normalization.
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional

logger = logging.getLogger(__name__)


class AIProvider(ABC):
    """Abstract base class for AI model providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider identifier (e.g. 'claude', 'openai')."""
        ...

    @property
    @abstractmethod
    def default_model(self) -> str:
        """Return the default model identifier."""
        ...

    @abstractmethod
    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 500,
    ) -> dict:
        """Generate text from the model.

        Returns:
            {
                "text": str,
                "provider": str,
                "model": str,
                "token_usage": {
                    "prompt_tokens": int | None,
                    "completion_tokens": int | None,
                    "total_tokens": int | None,
                }
            }
        """
        ...

    def _empty_response(self, error: str = "") -> dict:
        """Return a safe empty response on failure."""
        return {
            "text": error or "No response generated.",
            "provider": self.provider_name,
            "model": self.default_model,
            "token_usage": {
                "prompt_tokens": None,
                "completion_tokens": None,
                "total_tokens": None,
            },
        }
