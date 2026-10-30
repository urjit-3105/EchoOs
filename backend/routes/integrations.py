"""Third-party integration status, Google OAuth setup flow, and harmless test pings."""

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse

from config.settings import settings
from core.execution.plugins.calendar import build_authorization_url, exchange_code_for_tokens
from core.execution.registry import ToolRegistry
from core.llm.service import LLMService
from core.logger.structured import get_logger
from database import get_database

logger = get_logger(__name__)

router = APIRouter(prefix="/integrations", tags=["Integrations"])


@router.get("/")
async def list_integrations() -> List[Dict[str, Any]]:
    """Status of every integration - never returns secret values."""
    db = get_database()
    active_llm = LLMService.active_provider().name

    return [
        {"name": "email", "enabled": settings.enable_email, "configured": settings.smtp_enabled, "mode": "live" if settings.smtp_enabled else "simulated"},
        {"name": "slack", "enabled": settings.enable_slack, "configured": settings.slack_enabled, "mode": "live" if settings.slack_enabled else "simulated"},
        {"name": "jira", "enabled": settings.enable_jira, "configured": settings.jira_enabled, "mode": "live" if settings.jira_enabled else "simulated"},
        {
            "name": "calendar",
            "enabled": settings.enable_google_calendar,
            "configured": settings.google_calendar_enabled,
            "mode": "live" if settings.google_calendar_enabled else "simulated",
        },
        {"name": "supabase", "enabled": True, "configured": settings.supabase_enabled, "mode": db.name},
        {
            "name": "llm",
            "enabled": True,
            "configured": active_llm != "rules",
            "mode": active_llm,
        },
    ]


@router.get("/google/authorize")
async def google_authorize() -> RedirectResponse:
    """Redirects to Google's OAuth consent screen to mint a Calendar refresh token."""
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(status_code=400, detail="GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET are not configured.")
    return RedirectResponse(url=build_authorization_url())


@router.get("/google/callback")
async def google_callback(code: str = Query(...)) -> Dict[str, Any]:
    """Exchanges the OAuth code for tokens. Paste the returned refresh_token into .env as GOOGLE_REFRESH_TOKEN."""
    try:
        tokens = await exchange_code_for_tokens(code)
    except Exception as exc:  # noqa: BLE001 - surface the provider's error to the admin performing setup
        raise HTTPException(status_code=400, detail=f"Failed to exchange authorization code: {exc}") from exc

    refresh_token = tokens.get("refresh_token")
    return {
        "message": (
            "Copy the refresh_token below into your .env file as GOOGLE_REFRESH_TOKEN, "
            "then restart the app to enable live Google Calendar integration."
            if refresh_token
            else "No refresh_token was returned - Google only issues one on first consent. "
            "Revoke prior access at https://myaccount.google.com/permissions and try again."
        ),
        "refresh_token": refresh_token,
        "token_type": tokens.get("token_type"),
        "expires_in": tokens.get("expires_in"),
    }


@router.post("/{name}/test")
async def test_integration(name: str) -> Dict[str, Any]:
    """Fire a harmless health check through the named plugin and report the result."""
    try:
        plugin = ToolRegistry.get_plugin(name)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    healthy = await plugin.health()
    return {"name": name, "healthy": healthy, "tool_name": plugin.tool_name}
