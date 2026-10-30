"""Abstract contract every LLM provider implements.

Kept intentionally tiny: agents never talk to a provider directly, they go
through :class:`core.llm.service.LLMService`, so this ABC only needs to
describe what the service needs to try a provider and know if it can.
"""

from abc import ABC, abstractmethod
from typing import Optional


class LLMProvider(ABC):
    """A single LLM backend (Gemini, Groq, OpenAI, or the deterministic fallback)."""

    name: str = "base"

    @property
    @abstractmethod
    def available(self) -> bool:
        """Whether this provider has the configuration it needs (API key, etc.)."""
        raise NotImplementedError

    @abstractmethod
    async def complete(
        self,
        prompt: str,
        *,
        system: Optional[str] = None,
        json_mode: bool = False,
    ) -> str:
        """Return the model's text completion for ``prompt``.

        Implementations should raise on failure (timeout, HTTP error, bad
        payload) - the caller (:class:`LLMService`) is responsible for
        catching exceptions and falling back to the next provider.
        """
        raise NotImplementedError
