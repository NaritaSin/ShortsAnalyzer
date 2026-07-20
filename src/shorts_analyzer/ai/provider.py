"""Abstract AI provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod


class AIProvider(ABC):
    """Base class for text-generation AI providers."""

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Generate a text response from a prompt."""
        raise NotImplementedError
