"""Deterministic, zero-dependency provider.

This is the guaranteed fallback: it has no external calls and is always
``available``, so the platform produces sensible (if terse) reasoning text
even when no LLM API key is configured anywhere.
"""

import json
from typing import Optional

from core.llm.base import LLMProvider


class RuleBasedProvider(LLMProvider):
    name = "rules"

    @property
    def available(self) -> bool:
        return True

    async def complete(
        self,
        prompt: str,
        *,
        system: Optional[str] = None,
        json_mode: bool = False,
    ) -> str:
        """Return a short templated summary derived from the prompt text.

        There is no real "understanding" here - we just surface the first
        line of the prompt (typically the instruction/subject) so the UI has
        something readable instead of an empty field.
        """
        first_line = next((line.strip() for line in prompt.splitlines() if line.strip()), prompt.strip())
        if len(first_line) > 200:
            first_line = first_line[:197] + "..."

        summary = f"Automated summary: {first_line}" if first_line else "Automated summary: no details available."

        if json_mode:
            return json.dumps({"summary": summary, "provider": self.name})
        return summary
