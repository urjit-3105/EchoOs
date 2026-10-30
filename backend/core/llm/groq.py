"""Groq provider - OpenAI-compatible chat completions API, very low latency."""

from typing import Any, Dict, List, Optional

import httpx

from config.settings import settings
from core.llm.base import LLMProvider
from core.logger.structured import get_logger

logger = get_logger(__name__)


class GroqProvider(LLMProvider):
    name = "groq"

    @property
    def available(self) -> bool:
        return settings.groq_enabled

    async def complete(
        self,
        prompt: str,
        *,
        system: Optional[str] = None,
        json_mode: bool = False,
    ) -> str:
        url = "https://api.groq.com/openai/v1/chat/completions"

        messages: List[Dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        body: Dict[str, Any] = {"model": settings.groq_model, "messages": messages}
        if json_mode:
            body["response_format"] = {"type": "json_object"}

        headers = {"Authorization": f"Bearer {settings.groq_api_key}"}

        async with httpx.AsyncClient(timeout=settings.llm_timeout_seconds) as client:
            response = await client.post(url, json=body, headers=headers)
            response.raise_for_status()
            data = response.json()

        choices = data.get("choices") or []
        if not choices:
            raise ValueError("Groq returned no choices.")

        content = choices[0].get("message", {}).get("content", "")
        if not content:
            raise ValueError("Groq returned an empty completion.")
        return content
