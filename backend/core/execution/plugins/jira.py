"""JiraPlugin - raises and manages IT/onboarding tickets in Jira.

Live when ``settings.jira_enabled``, otherwise simulates a plausible ticket
key so downstream tasks (health checks, activation) never stall on a missing
Jira project.
"""

import itertools
from typing import Any, Dict

import httpx

from config.settings import settings
from core.execution.plugins.base import BasePlugin
from core.execution.plugins.http import request
from core.execution.registry import ToolRegistry
from core.logger.structured import get_logger

logger = get_logger(__name__)

# Monotonically increasing counter used only for simulated ticket keys - resets
# on process restart, which is fine since simulated tickets are not persisted.
_simulated_counter = itertools.count(101)


def _adf(text: str) -> Dict[str, Any]:
    """Wrap plain text in the Atlassian Document Format the Jira v3 API requires for descriptions/comments."""
    return {
        "type": "doc",
        "version": 1,
        "content": [{"type": "paragraph", "content": [{"type": "text", "text": text}]}],
    }


def _substitute(template: str, inputs: Dict[str, Any]) -> str:
    try:
        return template.format(
            employee_name=inputs.get("employee_name", "New Employee"),
            department=inputs.get("department", "General"),
            job_title=inputs.get("job_title", "Team Member"),
        )
    except (KeyError, IndexError):
        return template


@ToolRegistry.register("jira")
class JiraPlugin(BasePlugin):
    """Creates, transitions and comments on Jira issues via the REST API v3."""

    @property
    def tool_name(self) -> str:
        return "jira"

    async def connect(self) -> bool:
        return True

    async def validate(self, inputs: Dict[str, Any]) -> bool:
        action = inputs.get("action", "create_issue")
        if action in {"transition_issue", "add_comment"}:
            return bool(inputs.get("ticket_key") or inputs.get("issue_key"))
        return True

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        action = inputs.get("action", "create_issue")
        try:
            if action == "transition_issue":
                result = await self._transition_issue(inputs)
            elif action == "add_comment":
                result = await self._add_comment(inputs)
            else:
                result = await self._create_issue(inputs)
            await self._audit(action, inputs, result)
            return result
        except Exception as exc:
            logger.error("Jira plugin execution failed", context={"action": action}, exc_info=exc)
            result = {
                "status": "failed",
                "mode": "live" if settings.jira_enabled else "simulated",
                "error": str(exc),
            }
            await self._audit(action, inputs, result)
            return result

    async def rollback(self, execution_data: Dict[str, Any]) -> bool:
        if execution_data.get("mode") != "live":
            return True
        issue_id = execution_data.get("issue_id")
        if not issue_id or not settings.jira_enabled:
            return True
        try:
            response = await request(
                "DELETE",
                f"{settings.jira_base_url}/rest/api/3/issue/{issue_id}",
                auth=self._auth(),
            )
            return response.status_code in (200, 204)
        except Exception as exc:
            logger.error("Jira rollback (delete issue) failed", exc_info=exc)
            return False

    async def health(self) -> bool:
        return True

    # ------------------------------------------------------------------
    def _auth(self) -> httpx.BasicAuth:
        return httpx.BasicAuth(settings.jira_user_email, settings.jira_api_token)

    async def _create_issue(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        summary_template = inputs.get("summary_template", "Onboarding equipment for {employee_name}")
        summary = _substitute(summary_template, inputs)
        issue_type = inputs.get("issue_type", "Task")
        description = inputs.get("description") or (
            f"Automated onboarding ticket for {inputs.get('employee_name', 'a new employee')} "
            f"in {inputs.get('department', 'General')}."
        )

        if settings.jira_enabled:
            payload = {
                "fields": {
                    "project": {"key": settings.jira_project_key},
                    "summary": summary,
                    "issuetype": {"name": issue_type},
                    "description": _adf(description),
                }
            }
            response = await request(
                "POST",
                f"{settings.jira_base_url}/rest/api/3/issue",
                auth=self._auth(),
                json=payload,
            )
            if response.status_code not in (200, 201):
                return {
                    "status": "failed",
                    "mode": "live",
                    "error": f"Jira returned {response.status_code}: {response.text}",
                }
            data = response.json()
            key = data.get("key")
            return {
                "status": "success",
                "mode": "live",
                "ticket_key": key,
                "issue_id": data.get("id"),
                "url": f"{settings.jira_base_url}/browse/{key}",
                "details": f"Created Jira issue {key}.",
            }

        key = f"{settings.jira_project_key}-{next(_simulated_counter)}"
        return {
            "status": "success",
            "mode": "simulated",
            "ticket_key": key,
            "issue_id": f"sim-{key}",
            "url": f"https://simulated.atlassian.net/browse/{key}",
            "details": f"[SIMULATED] Created Jira issue {key}: {summary}",
        }

    async def _transition_issue(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        ticket_key = inputs.get("ticket_key") or inputs.get("issue_key")
        transition_name = inputs.get("transition_name", "Done")

        if settings.jira_enabled:
            transitions_resp = await request(
                "GET",
                f"{settings.jira_base_url}/rest/api/3/issue/{ticket_key}/transitions",
                auth=self._auth(),
            )
            transitions = transitions_resp.json().get("transitions", [])
            match = next((t for t in transitions if t["name"].lower() == transition_name.lower()), None)
            if not match:
                return {
                    "status": "failed",
                    "mode": "live",
                    "error": f"No transition named '{transition_name}' available on {ticket_key}.",
                }
            response = await request(
                "POST",
                f"{settings.jira_base_url}/rest/api/3/issue/{ticket_key}/transitions",
                auth=self._auth(),
                json={"transition": {"id": match["id"]}},
            )
            if response.status_code not in (200, 204):
                return {
                    "status": "failed",
                    "mode": "live",
                    "error": f"Jira returned {response.status_code}: {response.text}",
                }
            return {
                "status": "success",
                "mode": "live",
                "ticket_key": ticket_key,
                "details": f"Transitioned {ticket_key} to '{transition_name}'.",
            }

        return {
            "status": "success",
            "mode": "simulated",
            "ticket_key": ticket_key,
            "details": f"[SIMULATED] Transitioned {ticket_key} to '{transition_name}'.",
        }

    async def _add_comment(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        ticket_key = inputs.get("ticket_key") or inputs.get("issue_key")
        comment = inputs.get("comment", "Update from Echo WorkforceOS.")

        if settings.jira_enabled:
            response = await request(
                "POST",
                f"{settings.jira_base_url}/rest/api/3/issue/{ticket_key}/comment",
                auth=self._auth(),
                json={"body": _adf(comment)},
            )
            if response.status_code not in (200, 201):
                return {
                    "status": "failed",
                    "mode": "live",
                    "error": f"Jira returned {response.status_code}: {response.text}",
                }
            return {"status": "success", "mode": "live", "ticket_key": ticket_key, "details": f"Comment added to {ticket_key}."}

        return {
            "status": "success",
            "mode": "simulated",
            "ticket_key": ticket_key,
            "details": f"[SIMULATED] Comment added to {ticket_key}: {comment}",
        }

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
            logger.warning("Failed to record audit trail for jira plugin", exc_info=exc)
