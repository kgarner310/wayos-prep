"""Claude AI Provider — Anthropic Claude integration.

Uses the Anthropic API via the anthropic Python SDK. Requires
ANTHROPIC_API_KEY environment variable. Gracefully degrades if
the SDK is not installed or the key is not set.
"""

import logging
import os
from typing import Optional

from app.ai.providers.base_provider import AIProvider

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "claude-sonnet-4-20250514"


class ClaudeProvider(AIProvider):
    """Anthropic Claude provider."""

    def __init__(self, model: Optional[str] = None, api_key: Optional[str] = None):
        self._model = model or DEFAULT_MODEL
        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self._client = None

    @property
    def provider_name(self) -> str:
        return "claude"

    @property
    def default_model(self) -> str:
        return self._model

    def _get_client(self):
        """Lazy-init the Anthropic client."""
        if self._client is not None:
            return self._client
        if not self._api_key:
            logger.warning("ANTHROPIC_API_KEY not set — Claude provider unavailable")
            return None
        try:
            import anthropic
            self._client = anthropic.Anthropic(api_key=self._api_key)
            return self._client
        except ImportError:
            logger.warning("anthropic SDK not installed — Claude provider unavailable")
            return None

    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 500,
    ) -> dict:
        """Generate text using Claude API."""
        client = self._get_client()
        if client is None:
            return self._empty_response("Claude provider not available (no API key or SDK)")

        try:
            kwargs = {
                "model": self._model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [{"role": "user", "content": prompt}],
            }
            if system_prompt:
                kwargs["system"] = system_prompt

            response = client.messages.create(**kwargs)

            text = ""
            if response.content:
                text = response.content[0].text

            usage = response.usage if hasattr(response, "usage") else None

            return {
                "text": text,
                "provider": self.provider_name,
                "model": self._model,
                "token_usage": {
                    "prompt_tokens": getattr(usage, "input_tokens", None),
                    "completion_tokens": getattr(usage, "output_tokens", None),
                    "total_tokens": (
                        (getattr(usage, "input_tokens", 0) or 0)
                        + (getattr(usage, "output_tokens", 0) or 0)
                    ) if usage else None,
                },
            }
        except Exception as e:
            logger.error("Claude API call failed: %s", e)
            return self._empty_response(f"Claude API error: {str(e)}")
