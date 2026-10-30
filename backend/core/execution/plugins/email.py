"""EmailPlugin - delivers onboarding/notification email.

Delegates the actual send to ``services.email.EmailService`` (lazy import) so
the ``email_outbox`` table stays the single source of truth for every message
sent anywhere in the app, whether triggered by an agent or a human. This
plugin never opens its own SMTP connection.
"""

from typing import Any, Dict, Tuple

from core.execution.plugins.base import BasePlugin
from core.execution.registry import ToolRegistry
from core.logger.structured import get_logger

logger = get_logger(__name__)

# EmailService.send() records "sent" only when SMTP actually delivered the
# message; "simulated"/"queued" mean the outbox recorded it without a real
# SMTP attempt (the default in local development).
_LIVE_STATUSES = {"sent"}
_ACCEPTED_STATUSES = {"sent", "simulated", "queued"}


@ToolRegistry.register("email")
class EmailPlugin(BasePlugin):
    """Sends onboarding/notification email via the shared outbox-backed EmailService."""

    @property
    def tool_name(self) -> str:
        return "email"

    async def connect(self) -> bool:
        return True

    async def validate(self, inputs: Dict[str, Any]) -> bool:
        if not inputs.get("to"):
            return False
        if not inputs.get("template") and not inputs.get("subject"):
            return False
        return True

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        action = inputs.get("action", "send")
        to = inputs.get("to", "")
        template = inputs.get("template")
        try:
            subject, html, text = self._render(template, inputs)

            from services.email import EmailService

            row = await EmailService.send(to=to, subject=subject, html=html, text=text, template=template)
            row_status = row.get("status", "queued")
            mode = "live" if row_status in _LIVE_STATUSES else "simulated"
            success = row_status in _ACCEPTED_STATUSES

            result: Dict[str, Any] = {
                "status": "success" if success else "failed",
                "mode": mode,
                "message_id": row.get("id"),
                "details": f"Email '{subject}' to {to} is {row_status} ({mode}).",
            }
            if not success:
                result["error"] = row.get("error_message") or "Email delivery failed."
            await self._audit(action, inputs, result)
            return result
        except Exception as exc:
            logger.error("Email plugin execution failed", context={"to": to}, exc_info=exc)
            result = {"status": "failed", "mode": "simulated", "error": str(exc)}
            await self._audit(action, inputs, result)
            return result

    async def rollback(self, execution_data: Dict[str, Any]) -> bool:
        # Emails cannot be unsent once dispatched - an intentional, explanatory no-op.
        logger.info(
            "Email rollback requested; emails cannot be recalled once sent, treating as a no-op.",
            context={"message_id": execution_data.get("message_id")},
        )
        return True

    async def health(self) -> bool:
        return True  # simulation (SMTP disabled) always counts as healthy

    # ------------------------------------------------------------------
    def _render(self, template: Any, inputs: Dict[str, Any]) -> Tuple[str, str, str]:
        """Build (subject, html, text) using an EmailService builder when the template names one."""
        employee_name = inputs.get("employee_name", "there")
        organization_name = inputs.get("organization_name", "Echo WorkforceOS")

        if template == "welcome":
            from services.email import EmailService

            subject, html = EmailService.welcome_email(
                employee_name=employee_name,
                org_name=organization_name,
                corporate_email=inputs.get("corporate_email", ""),
                portal_url=inputs.get("portal_url", ""),
            )
            return subject, html, subject

        if template == "invitation":
            from services.email import EmailService

            subject, html = EmailService.invitation_email(
                employee_name=employee_name,
                org_name=organization_name,
                accept_url=inputs.get("portal_url", ""),
                expires_at=inputs.get("expires_at", "soon"),
            )
            return subject, html, subject

        # "generic" (or any unrecognised template name) - fall back to explicit subject/body.
        subject = inputs.get("subject") or f"Update from {organization_name}"
        body = inputs.get("body") or inputs.get("body_text") or subject
        html = inputs.get("body_html") or f"<p>{body}</p>"
        return subject, html, body

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
            logger.warning("Failed to record audit trail for email plugin", exc_info=exc)
