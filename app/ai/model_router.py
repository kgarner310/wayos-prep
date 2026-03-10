"""Model Router — decides which AI provider/model to use for each task.

Routes task types to the appropriate provider. Logs all AI usage
for telemetry. Falls back gracefully when no provider is available.
"""

import logging
from typing import Optional

from app.ai.providers.base_provider import AIProvider
from app.ai.providers.claude_provider import ClaudeProvider

logger = logging.getLogger(__name__)

# Default task-to-provider routing
_DEFAULT_ROUTES: dict[str, str] = {
    "rewrite_response": "claude",
    "meeting_summary": "claude",
    "explanation": "claude",
    "experimental": "claude",
    "service_triage": "claude",
}


class ModelRouter:
    """Routes AI tasks to the appropriate provider and model."""

    def __init__(self):
        self._providers: dict[str, AIProvider] = {}
        self._routes: dict[str, str] = dict(_DEFAULT_ROUTES)
        self._register_default_providers()

    def _register_default_providers(self):
        """Register available providers."""
        try:
            claude = ClaudeProvider()
            self._providers["claude"] = claude
        except Exception:
            logger.debug("Claude provider registration failed", exc_info=True)

    def register_provider(self, name: str, provider: AIProvider):
        """Register a custom provider."""
        self._providers[name] = provider

    def set_route(self, task_type: str, provider_name: str):
        """Override the routing for a task type."""
        self._routes[task_type] = provider_name

    def get_provider(self, task_type: str) -> Optional[AIProvider]:
        """Get the provider for a given task type."""
        provider_name = self._routes.get(task_type, "claude")
        return self._providers.get(provider_name)

    def generate_text(
        self,
        task_type: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 500,
        office_id: Optional[str] = None,
        endpoint: Optional[str] = None,
    ) -> dict:
        """Route a text generation request to the appropriate provider.

        Logs usage telemetry for every call.
        """
        provider = self.get_provider(task_type)
        if provider is None:
            logger.warning("No provider available for task_type=%s", task_type)
            return {
                "text": "",
                "provider": "none",
                "model": "none",
                "token_usage": {
                    "prompt_tokens": None,
                    "completion_tokens": None,
                    "total_tokens": None,
                },
                "error": f"No provider configured for task_type '{task_type}'",
            }

        result = provider.generate_text(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # Log AI usage telemetry (non-blocking)
        try:
            from app.telemetry.ai_usage import record_ai_usage
            record_ai_usage(
                provider=result.get("provider", "unknown"),
                model=result.get("model", "unknown"),
                task_type=task_type,
                token_usage=result.get("token_usage", {}),
                office_id=office_id,
                endpoint=endpoint,
            )
        except Exception:
            logger.debug("Failed to record AI usage telemetry", exc_info=True)

        return result


# Module-level singleton for convenience
_router: Optional[ModelRouter] = None


def get_model_router() -> ModelRouter:
    """Get or create the global model router singleton."""
    global _router
    if _router is None:
        _router = ModelRouter()
    return _router
