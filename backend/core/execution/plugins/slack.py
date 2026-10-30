"""SlackPlugin - announces new hires and invites them to team channels.

Live when ``settings.slack_enabled``, otherwise falls back to a fully audited
simulation with the same return shape so a missing bot token never breaks the
onboarding demo.
"""

import time
from typing import Any, Dict, List

from config.settings import settings
from core.execution.plugins.base import BasePlugin
from core.execution.plugins.http import request
from core.execution.registry import ToolRegistry
from core.logger.structured import get_logger

logger = get_logger(__name__)

SLACK_API = "https://slack.com/api"


@ToolRegistry.register("slack")
class SlackPlugin(BasePlugin):
    """Posts onboarding announcements and channel invites to Slack via the Bot API."""

    @property
    def tool_name(self) -> str:
        return "slack"

    async def connect(self) -> bool:
        return True

    async def validate(self, inputs: Dict[str, Any]) -> bool:
        return True  # channel/user_id both have sensible defaults/fallbacks

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        action = inputs.get("action", "post_message")
        try:
            if action == "invite_user":
                result = await self._invite_user(inputs)
            else:
                result = await self._post_message(inputs)
            await self._audit(action, inputs, result)
            return result
        except Exception as exc:
            logger.error("Slack plugin execution failed", context={"action": action}, exc_info=exc)
            result = {
                "status": "failed",
                "mode": "live" if settings.slack_enabled else "simulated",
                "error": str(exc),
            }
            await self._audit(action, inputs, result)
            return result

    async def rollback(self, execution_data: Dict[str, Any]) -> bool:
        if execution_data.get("mode") != "live":
            return True
        channel = execution_data.get("channel")
        ts = execution_data.get("message_ts")
        if not (channel and ts and settings.slack_enabled):
            return True
        try:
            response = await request(
                "POST",
                f"{SLACK_API}/chat.delete",
                headers=self._headers(),
                json={"channel": channel, "ts": ts},
            )
            data = response.json()
            return bool(data.get("ok"))
        except Exception as exc:
            logger.error("Slack rollback (chat.delete) failed", exc_info=exc)
            return False

    async def health(self) -> bool:
        return True  # simulation is always healthy; live failures surface per-call

    # ------------------------------------------------------------------
    def _headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {settings.slack_bot_token}", "Content-Type": "application/json"}

    def _welcome_blocks(self, inputs: Dict[str, Any]) -> List[Dict[str, Any]]:
        name = inputs.get("employee_name", "our newest teammate")
        title = inputs.get("job_title")
        dept = inputs.get("department")
        role_line = " · ".join(part for part in (title, dept) if part)
        text = f":tada: Please welcome *{name}*" + (f" ({role_line})" if role_line else "") + " to the team!"
        return [{"type": "section", "text": {"type": "mrkdwn", "text": text}}]

    async def _post_message(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        channel = inputs.get("channel") or settings.slack_default_channel
        blocks = self._welcome_blocks(inputs)
        text = inputs.get("message") or f"Welcome {inputs.get('employee_name', 'to the team')}!"

        if settings.slack_enabled:
            response = await request(
                "POST",
                f"{SLACK_API}/chat.postMessage",
                headers=self._headers(),
                json={"channel": channel, "text": text, "blocks": blocks},
            )
            data = response.json()
            if not data.get("ok"):
                return {"status": "failed", "mode": "live", "error": data.get("error", "unknown_slack_error")}
            return {
                "status": "success",
                "mode": "live",
                "channel": data.get("channel", channel),
                "message_ts": data.get("ts"),
                "details": f"Posted welcome message to {channel}.",
            }

        message_ts = f"{time.time():.6f}"
        return {
            "status": "success",
            "mode": "simulated",
            "channel": channel,
            "message_ts": message_ts,
            "details": f"[SIMULATED] Would post welcome message to {channel}.",
        }

    async def _invite_user(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        channel = inputs.get("channel") or settings.slack_default_channel
        user_id = inputs.get("user_id")

        if not user_id:
            # No Slack user id yet - fall back to a posted announcement instead.
            return await self._post_message(inputs)

        if settings.slack_enabled:
            response = await request(
                "POST",
                f"{SLACK_API}/conversations.invite",
                headers=self._headers(),
                json={"channel": channel, "users": user_id},
            )
            data = response.json()
            if not data.get("ok"):
                return {"status": "failed", "mode": "live", "error": data.get("error", "unknown_slack_error")}
            return {
                "status": "success",
                "mode": "live",
                "channel": channel,
                "message_ts": None,
                "details": f"Invited {user_id} to {channel}.",
            }

        return {
            "status": "success",
            "mode": "simulated",
            "channel": channel,
            "message_ts": f"{time.time():.6f}",
            "details": f"[SIMULATED] Would invite {user_id} to {channel}.",
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
            logger.warning("Failed to record audit trail for slack plugin", exc_info=exc)
