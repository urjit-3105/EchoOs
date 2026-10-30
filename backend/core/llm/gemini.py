"""Google Gemini provider - free-tier friendly, so it is first in the ``auto`` chain."""

from typing import Any, Dict, Optional

import httpx

from config.settings import settings
from core.llm.base import LLMProvider
from core.logger.structured import get_logger

logger = get_logger(__name__)


class GeminiProvider(LLMProvider):
    name = "gemini"

    @property
    def available(self) -> bool:
        return settings.gemini_enabled

    async def complete(
        self,
        prompt: str,
        *,
        system: Optional[str] = None,
        json_mode: bool = False,
    ) -> str:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{settings.gemini_model}:generateContent?key={settings.gemini_api_key}"
        )

        generation_config: Dict[str, Any] = {}
        if json_mode:
            generation_config["response_mime_type"] = "application/json"

        body: Dict[str, Any] = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": generation_config,
        }
        if system:
            body["system_instruction"] = {"parts": [{"text": system}]}

        async with httpx.AsyncClient(timeout=settings.llm_timeout_seconds) as client:
            response = await client.post(url, json=body)
            response.raise_for_status()
            data = response.json()

        candidates = data.get("candidates") or []
        if not candidates:
            raise ValueError("Gemini returned no candidates.")

        parts = candidates[0].get("content", {}).get("parts", [])
        text = "".join(part.get("text", "") for part in parts)
        if not text:
            raise ValueError("Gemini returned an empty completion.")
        return text
