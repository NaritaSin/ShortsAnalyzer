"""OpenAI-backed AI provider (placeholder implementation)."""

from __future__ import annotations

from shorts_analyzer.ai.provider import AIProvider


class OpenAIProvider(AIProvider):
    """Placeholder OpenAI provider for future API integration."""

    def generate(self, prompt: str) -> str:
        """Return a dummy response without calling an external API."""
        preview = prompt.strip().splitlines()[0] if prompt.strip() else "empty prompt"
        return f"[OpenAI placeholder response for: {preview}]"
