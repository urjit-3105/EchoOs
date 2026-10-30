"""Provider-agnostic LLM facade used by every agent that needs reasoning text.

Agents never import a concrete provider - they call :class:`LLMService`,
which tries providers in order and always degrades gracefully to the
deterministic :class:`~core.llm.rules.RuleBasedProvider`. An LLM error must
never propagate out of this module; every failure is logged and swallowed.
"""

import asyncio
import json
import re
from typing import Any, Dict, List, Optional

from config.settings import settings
from core.llm.base import LLMProvider
from core.logger.structured import get_logger

logger = get_logger(__name__)

_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)


class LLMService:
    """Static facade coordinating provider selection, timeouts and fallbacks."""

    @staticmethod
    def providers() -> List[LLMProvider]:
        """Ordered provider chain.

        ``auto`` tries every real provider (in the order most likely to be
        free/available) before the deterministic fallback. An explicit
        ``settings.llm_provider`` pins that provider first, with the rule
        engine kept as the last resort so the pinned choice being
        unconfigured never breaks agents.
        """
        from core.llm.gemini import GeminiProvider
        from core.llm.groq import GroqProvider
        from core.llm.openai import OpenAIProvider
        from core.llm.rules import RuleBasedProvider

        gemini, groq, openai_, rules = GeminiProvider(), GroqProvider(), OpenAIProvider(), RuleBasedProvider()

        chain: Dict[str, LLMProvider] = {
            "gemini": gemini,
            "groq": groq,
            "openai": openai_,
            "rules": rules,
        }

        choice = (settings.llm_provider or "auto").lower()
        if choice == "auto" or choice not in chain:
            return [gemini, groq, openai_, rules]

        ordered = [chain[choice]] + [p for key, p in chain.items() if key != choice and key != "rules"]
        ordered.append(rules)
        return ordered

    @staticmethod
    def active_provider() -> LLMProvider:
        """First provider that reports itself as available (rules always is)."""
        for provider in LLMService.providers():
            if provider.available:
                return provider
        from core.llm.rules import RuleBasedProvider

        return RuleBasedProvider()

    @staticmethod
    async def complete(
        prompt: str,
        *,
        system: Optional[str] = None,
        json_mode: bool = False,
        fallback: str = "",
    ) -> str:
        """Try every available provider in order, returning ``fallback`` if all fail."""
        for provider in LLMService.providers():
            if not provider.available:
                continue
            try:
                return await asyncio.wait_for(
                    provider.complete(prompt, system=system, json_mode=json_mode),
                    timeout=settings.llm_timeout_seconds,
                )
            except Exception as exc:  # noqa: BLE001 - any provider failure just moves on
                logger.warning(
                    f"LLM provider '{provider.name}' failed, trying next.",
                    context={"error": str(exc)},
                )
                continue

        logger.error("All LLM providers failed or are unavailable; returning fallback text.")
        return fallback

    @staticmethod
    async def complete_json(
        prompt: str,
        *,
        system: Optional[str] = None,
        default: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Complete and parse the result as JSON, tolerating ```json fences and stray text."""
        default = default if default is not None else {}
        raw = await LLMService.complete(prompt, system=system, json_mode=True, fallback="")
        if not raw:
            return default

        candidate = raw.strip()
        fence_match = _JSON_FENCE_RE.search(candidate)
        if fence_match:
            candidate = fence_match.group(1).strip()

        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
            return {"value": parsed}
        except (json.JSONDecodeError, TypeError) as exc:
            logger.warning("Failed to parse LLM JSON response; using default.", context={"error": str(exc)})
            return default

    # ------------------------------------------------------------------
    # Domain-specific helpers used by agents
    # ------------------------------------------------------------------
    @staticmethod
    async def summarize_verification(report: Dict[str, Any], employee: Dict[str, Any]) -> str:
        """One short paragraph explaining the verification outcome, for the UI."""
        name = f"{employee.get('first_name', '')} {employee.get('last_name', '')}".strip() or "The candidate"
        status = report.get("overall_status", "pending")
        fallback = (
            f"{name}'s verification finished with status '{status}'. "
            f"Missing documents: {len(report.get('missing_documents') or [])}, "
            f"compliance findings: {len(report.get('compliance_findings') or [])}."
        )
        prompt = (
            "Summarize this employee onboarding verification report in one short, plain-English "
            f"paragraph for an HR reviewer.\nEmployee: {name}\nReport: {json.dumps(report, default=str)}"
        )
        return await LLMService.complete(
            prompt,
            system="You are a concise HR compliance assistant. Reply with one short paragraph, no markdown.",
            fallback=fallback,
        )

    @staticmethod
    async def summarize_plan(plan: Dict[str, Any]) -> str:
        """Short human summary of an execution plan, e.g. for a status page."""
        task_count = len(plan.get("tasks") or {})
        fallback = (
            f"This plan has {task_count} tasks with an estimated total duration of "
            f"{plan.get('estimated_total_duration', 0)} seconds."
        )
        prompt = f"Summarize this workflow execution plan in one short sentence:\n{json.dumps(plan, default=str)}"
        return await LLMService.complete(
            prompt,
            system="You are a concise workflow assistant. Reply with one short sentence, no markdown.",
            fallback=fallback,
        )

    @staticmethod
    async def explain_failure(task_name: str, error: str) -> str:
        """Human-readable explanation of why a task failed, for logs/notifications."""
        fallback = f"Task '{task_name}' failed: {error}"
        prompt = f"Explain in one short sentence why the onboarding task '{task_name}' failed: {error}"
        return await LLMService.complete(
            prompt,
            system="You are a concise technical assistant. Reply with one short sentence, no markdown.",
            fallback=fallback,
        )

    @staticmethod
    async def draft_approval_reason(employee: Dict[str, Any], report: Dict[str, Any]) -> str:
        """Draft the human-readable reason attached to an approval request."""
        name = f"{employee.get('first_name', '')} {employee.get('last_name', '')}".strip() or "the candidate"
        status = report.get("overall_status", "pending")
        fallback = (
            f"Manual review requested for {name}: verification status is '{status}'. "
            "Please review the findings before onboarding proceeds."
        )
        prompt = (
            f"Draft one short sentence explaining to an HR manager why {name}'s onboarding needs manual "
            f"approval. Verification report: {json.dumps(report, default=str)}"
        )
        return await LLMService.complete(
            prompt,
            system="You are a concise HR compliance assistant. Reply with one short sentence, no markdown.",
            fallback=fallback,
        )
