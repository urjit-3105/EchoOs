"""Shared HTTP helper for plugins that call external REST APIs.

Centralises the timeout and transport-error logging so every live
integration (Slack, Jira, Google Calendar) fails the same predictable,
audited way when the network or the remote API misbehaves, instead of each
plugin reinventing its own ``httpx.AsyncClient`` setup.
"""

from typing import Any

import httpx

from core.logger.structured import get_logger

logger = get_logger(__name__)

DEFAULT_TIMEOUT_SECONDS = 20


async def request(method: str, url: str, **kwargs: Any) -> httpx.Response:
    """Issue one HTTP request with a bounded timeout, logging transport failures.

    Returns the raw ``httpx.Response`` on success - callers still inspect
    ``response.status_code`` / parse JSON themselves, since some providers
    (Slack in particular) return HTTP 200 even on business-logic failures.
    Transport-level failures (DNS, timeout, connection refused) are logged
    here and re-raised so the caller's own ``try/except`` in ``execute()``
    turns them into a ``failed`` result dict rather than crashing the event
    loop.
    """
    timeout = kwargs.pop("timeout", DEFAULT_TIMEOUT_SECONDS)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            return await client.request(method, url, **kwargs)
        except httpx.HTTPError as exc:
            logger.error(
                "HTTP request to external integration failed",
                context={"method": method, "url": url},
                exc_info=exc,
            )
            raise
