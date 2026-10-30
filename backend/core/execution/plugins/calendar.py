"""CalendarPlugin - books, lists and cancels onboarding events on Google Calendar.

Live when ``settings.google_calendar_enabled`` (a refresh token is present),
otherwise simulates the same event shape with a synthetic id. Also exposes
the module-level OAuth helpers the (separate) integrations route uses to mint
a refresh token in the first place.
"""

import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from urllib.parse import urlencode

from config.settings import settings
from core.execution.plugins.base import BasePlugin
from core.execution.plugins.http import request
from core.execution.registry import ToolRegistry
from core.logger.structured import get_logger

logger = get_logger(__name__)

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_EVENTS_URL = "https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events"
CALENDAR_SCOPE = "https://www.googleapis.com/auth/calendar"

# In-memory access-token cache, refreshed ~60s before expiry. Fine for a
# single-process deployment; a multi-worker deployment would move this to a
# shared cache, but that is outside the scope of this plugin.
_token_cache: Dict[str, Any] = {"access_token": None, "expires_at": 0.0}


def build_authorization_url(state: Optional[str] = None) -> str:
    """Builds the Google OAuth consent URL. Used by the integrations route to mint a refresh token."""
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": CALENDAR_SCOPE,
        "access_type": "offline",
        "prompt": "consent",
    }
    if state:
        params["state"] = state
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


async def exchange_code_for_tokens(code: str) -> Dict[str, Any]:
    """Exchanges an OAuth authorization code for access/refresh tokens (one-time admin setup flow)."""
    response = await request(
        "POST",
        GOOGLE_TOKEN_URL,
        data={
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "code": code,
            "redirect_uri": settings.google_redirect_uri,
            "grant_type": "authorization_code",
        },
    )
    response.raise_for_status()
    return response.json()


async def _get_access_token() -> str:
    """Refreshes (and caches) the Google Calendar access token from the configured refresh token."""
    now = time.time()
    if _token_cache["access_token"] and _token_cache["expires_at"] - 60 > now:
        return _token_cache["access_token"]

    response = await request(
        "POST",
        GOOGLE_TOKEN_URL,
        data={
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "refresh_token": settings.google_refresh_token,
            "grant_type": "refresh_token",
        },
    )
    response.raise_for_status()
    data = response.json()
    _token_cache["access_token"] = data["access_token"]
    _token_cache["expires_at"] = now + data.get("expires_in", 3600)
    return _token_cache["access_token"]


def _substitute(template: str, inputs: Dict[str, Any]) -> str:
    try:
        return template.format(
            employee_name=inputs.get("employee_name", "New Employee"),
            department=inputs.get("department", "General"),
            job_title=inputs.get("job_title", "Team Member"),
        )
    except (KeyError, IndexError):
        return template


def _default_window(inputs: Dict[str, Any]) -> Dict[str, datetime]:
    """Start = the employee's start_date at 10:00 UTC, else tomorrow 10:00 UTC; end = start + duration."""
    duration = int(inputs.get("duration_minutes", 60))
    raw_start_date = inputs.get("start_date") or inputs.get("employee_start_date")

    start: Optional[datetime] = None
    if raw_start_date:
        try:
            parsed = datetime.fromisoformat(str(raw_start_date).replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            start = parsed.replace(hour=10, minute=0, second=0, microsecond=0)
        except ValueError:
            start = None

    if start is None:
        start = (datetime.now(timezone.utc) + timedelta(days=1)).replace(
            hour=10, minute=0, second=0, microsecond=0
        )

    return {"start": start, "end": start + timedelta(minutes=duration)}


@ToolRegistry.register("calendar")
class CalendarPlugin(BasePlugin):
    """Books onboarding calendar events on Google Calendar, or simulates them when unconfigured."""

    @property
    def tool_name(self) -> str:
        return "calendar"

    async def connect(self) -> bool:
        return True

    async def validate(self, inputs: Dict[str, Any]) -> bool:
        return True  # every field has a documented default

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        action = inputs.get("action", "create_event")
        try:
            if action == "delete_event":
                result = await self._delete_event(inputs)
            elif action == "list_events":
                result = await self._list_events(inputs)
            else:
                result = await self._create_event(inputs)
            await self._audit(action, inputs, result)
            return result
        except Exception as exc:
            logger.error("Calendar plugin execution failed", context={"action": action}, exc_info=exc)
            result = {
                "status": "failed",
                "mode": "live" if settings.google_calendar_enabled else "simulated",
                "error": str(exc),
            }
            await self._audit(action, inputs, result)
            return result

    async def rollback(self, execution_data: Dict[str, Any]) -> bool:
        if execution_data.get("mode") != "live":
            return True
        event_id = execution_data.get("event_id")
        if not event_id or not settings.google_calendar_enabled:
            return True
        try:
            token = await _get_access_token()
            url = f"{GOOGLE_EVENTS_URL.format(calendar_id=settings.google_calendar_id)}/{event_id}"
            response = await request("DELETE", url, headers={"Authorization": f"Bearer {token}"})
            return response.status_code in (200, 204)
        except Exception as exc:
            logger.error("Calendar rollback (delete event) failed", exc_info=exc)
            return False

    async def health(self) -> bool:
        return True

    # ------------------------------------------------------------------
    async def _create_event(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        window = _default_window(inputs)
        summary = _substitute(inputs.get("summary_template", "Orientation - {employee_name}"), inputs)
        description = inputs.get("description", "Automated onboarding event scheduled by Echo WorkforceOS.")

        attendees = list(inputs.get("attendees") or [])
        employee_email = inputs.get("employee_email") or inputs.get("corporate_email")
        if employee_email and employee_email not in attendees:
            attendees.append(employee_email)

        if settings.google_calendar_enabled:
            token = await _get_access_token()
            payload = {
                "summary": summary,
                "description": description,
                "start": {"dateTime": window["start"].isoformat(), "timeZone": "UTC"},
                "end": {"dateTime": window["end"].isoformat(), "timeZone": "UTC"},
                "attendees": [{"email": email} for email in attendees],
            }
            url = GOOGLE_EVENTS_URL.format(calendar_id=settings.google_calendar_id)
            response = await request("POST", url, headers={"Authorization": f"Bearer {token}"}, json=payload)
            if response.status_code not in (200, 201):
                return {
                    "status": "failed",
                    "mode": "live",
                    "error": f"Google Calendar returned {response.status_code}: {response.text}",
                }
            data = response.json()
            return {
                "status": "success",
                "mode": "live",
                "event_id": data.get("id"),
                "event_link": data.get("htmlLink"),
                "start": window["start"].isoformat(),
                "end": window["end"].isoformat(),
                "details": f"Created calendar event '{summary}'.",
            }

        event_id = str(uuid.uuid4())
        return {
            "status": "success",
            "mode": "simulated",
            "event_id": event_id,
            "event_link": f"https://calendar.simulated.local/event/{event_id}",
            "start": window["start"].isoformat(),
            "end": window["end"].isoformat(),
            "details": f"[SIMULATED] Created calendar event '{summary}'.",
        }

    async def _delete_event(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        event_id = inputs.get("event_id")
        if settings.google_calendar_enabled and event_id:
            token = await _get_access_token()
            url = f"{GOOGLE_EVENTS_URL.format(calendar_id=settings.google_calendar_id)}/{event_id}"
            response = await request("DELETE", url, headers={"Authorization": f"Bearer {token}"})
            if response.status_code not in (200, 204):
                return {
                    "status": "failed",
                    "mode": "live",
                    "error": f"Google Calendar returned {response.status_code}: {response.text}",
                }
            return {"status": "success", "mode": "live", "event_id": event_id, "details": f"Deleted calendar event {event_id}."}

        return {
            "status": "success",
            "mode": "simulated",
            "event_id": event_id,
            "details": f"[SIMULATED] Deleted calendar event {event_id}.",
        }

    async def _list_events(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        if settings.google_calendar_enabled:
            token = await _get_access_token()
            url = GOOGLE_EVENTS_URL.format(calendar_id=settings.google_calendar_id)
            response = await request(
                "GET",
                url,
                headers={"Authorization": f"Bearer {token}"},
                params={"maxResults": inputs.get("max_results", 10)},
            )
            if response.status_code != 200:
                return {
                    "status": "failed",
                    "mode": "live",
                    "error": f"Google Calendar returned {response.status_code}: {response.text}",
                }
            data = response.json()
            return {"status": "success", "mode": "live", "events": data.get("items", []), "details": "Listed calendar events."}

        return {"status": "success", "mode": "simulated", "events": [], "details": "[SIMULATED] No events to list."}

    async def _audit(self, action: str, inputs: Dict[str, Any], result: Dict[str, Any]) -> None:
        try:
            from services.audit import AuditService

            await AuditService.record(
                action=f"plugin.{self.tool_name}.{action}",
                resource_type="integration",
                resource_id=inputs.get("employee_id") or inputs.get("workflow_id") or "system",
                actor=self.tool_name,
                actor_type="agent",
                changes=result,
            )
        except Exception as exc:
            logger.warning("Failed to record audit trail for calendar plugin", exc_info=exc)
