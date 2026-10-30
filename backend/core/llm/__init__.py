"""Pluggable LLM layer - agents should only ever import :class:`LLMService`."""

from core.llm.service import LLMService

__all__ = ["LLMService"]
