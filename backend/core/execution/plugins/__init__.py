"""Registers every execution plugin and exposes a machine-readable catalogue.

Importing this package (``import core.execution.plugins``, as ``main.py``
already does) is the one line the app needs to populate the ``ToolRegistry``;
nothing else has to import the individual plugin modules directly.

``PLUGIN_CATALOG`` is consumed by the ``/api/v1/agents/tools`` endpoint so the
UI can show which integrations are live vs. simulated without reaching into
plugin internals.
"""

from typing import Any, Dict, List

from config.settings import settings

import core.execution.plugins.email  # noqa: F401
import core.execution.plugins.slack  # noqa: F401
import core.execution.plugins.jira  # noqa: F401
import core.execution.plugins.calendar  # noqa: F401
import core.execution.plugins.storage  # noqa: F401
import core.execution.plugins.identity  # noqa: F401


def _mode(configured: bool) -> str:
    return "live" if configured else "simulated"


def _storage_mode() -> str:
    """Mirrors StoragePlugin's own mode logic: supabase -> live, sqlalchemy -> local."""
    try:
        from database import db

        adapter_name = getattr(db, "name", "simulated")
    except Exception:
        adapter_name = "simulated"
    if adapter_name == "supabase":
        return "live"
    if adapter_name == "sqlalchemy":
        return "local"
    return "simulated"


PLUGIN_CATALOG: List[Dict[str, Any]] = [
    {
        "name": "email",
        "display_name": "Email",
        "description": "Sends onboarding and notification email via the shared outbox-backed EmailService.",
        "mode": _mode(settings.smtp_enabled),
        "configured": settings.smtp_enabled,
        "actions": ["send"],
    },
    {
        "name": "slack",
        "display_name": "Slack",
        "description": "Posts onboarding announcements and channel invites to Slack.",
        "mode": _mode(settings.slack_enabled),
        "configured": settings.slack_enabled,
        "actions": ["post_message", "invite_user"],
    },
    {
        "name": "jira",
        "display_name": "Jira",
        "description": "Creates and manages IT/onboarding tickets in Jira.",
        "mode": _mode(settings.jira_enabled),
        "configured": settings.jira_enabled,
        "actions": ["create_issue", "transition_issue", "add_comment"],
    },
    {
        "name": "calendar",
        "display_name": "Google Calendar",
        "description": "Books, lists and cancels onboarding events on Google Calendar.",
        "mode": _mode(settings.google_calendar_enabled),
        "configured": settings.google_calendar_enabled,
        "actions": ["create_event", "delete_event", "list_events"],
    },
    {
        "name": "storage",
        "display_name": "Storage",
        "description": "Provisions employee workspaces and archives documents via the app's storage adapter.",
        "mode": _storage_mode(),
        "configured": True,
        "actions": ["provision_workspace", "upload", "archive_documents"],
    },
    {
        "name": "identity",
        "display_name": "Identity",
        "description": "Provisions corporate identities, group memberships and account lifecycle - always live.",
        "mode": "live",
        "configured": True,
        "actions": ["create_account", "activate_account", "deactivate_account", "assign_groups"],
    },
]

__all__ = ["PLUGIN_CATALOG"]
