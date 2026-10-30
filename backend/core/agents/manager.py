"""Real Manager Agent.

Sits at the human approval gate. Most runs never need a human at all - the
gate auto-approves when the verification report is clean (or when the
organization has turned off manual approval) - but anything ambiguous is
handed to a real reviewer via the approvals workflow, and the orchestrator
pauses until that approval resolves.
"""

from typing import Any, Dict, Optional

from config.settings import settings
from core.agents.base import BaseAgent
from core.orchestrator.registry import AgentRegistry
from core.state.models import ContextState
from core.logger.structured import get_logger

logger = get_logger(__name__)


@AgentRegistry.register("ManagerAgent")
class ManagerAgent(BaseAgent):
    """Evaluates the approval condition for a task and gates or auto-approves it."""

    def __init__(self):
        super().__init__(
            name="Manager Agent",
            capabilities=["human_escalation", "approval_processing", "reminders", "policy_override"],
        )

    async def validate(self, context: ContextState) -> bool:
        return True

    async def execute(self, context: ContextState) -> Dict[str, Any]:
        task = context.current_task
        workflow_id = context.workflow_id
        condition = (task.input_data or {}).get("approval_condition", "always")

        latest_report = await self._latest_verification_report(workflow_id)

        if not settings.require_manager_approval:
            reasoning = "Manager approval is disabled for this organization; auto-approving."
            self.log_execution("auto_approved", {"workflow_id": workflow_id, "reason": reasoning})
            return {
                "status": "success",
                "approved": True,
                "auto_approved": True,
                "reviewer": "Verification Agent (auto)",
                "reasoning": reasoning,
            }

        should_gate = self._should_gate(condition, latest_report)

        if not should_gate:
            reasoning = (
                "Verification passed cleanly; no human review required."
                if condition == "verification_not_passed"
                else "Approval condition does not require a human gate; auto-approving."
            )
            self.log_execution("auto_approved", {"workflow_id": workflow_id, "condition": condition})
            return {
                "status": "success",
                "approved": True,
                "auto_approved": True,
                "reviewer": "Verification Agent (auto)",
                "reasoning": reasoning,
            }

        return await self._gate(context, latest_report)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _should_gate(condition: str, report: Optional[Dict[str, Any]]) -> bool:
        if condition == "never":
            return False
        if condition == "verification_not_passed":
            status = (report or {}).get("overall_status")
            return status != "passed"
        # "always" (default) - always gate
        return True

    @staticmethod
    async def _latest_verification_report(workflow_id: str) -> Optional[Dict[str, Any]]:
        try:
            from repositories.verification_reports import verification_reports

            rows = await verification_reports.list(
                workflow_id=workflow_id, order_by="created_at", descending=True, limit=1
            )
            return rows[0] if rows else None
        except Exception as exc:  # noqa: BLE001 - missing report should not crash the gate
            logger.warning("Could not load latest verification report.", context={"error": str(exc)})
            return None

    async def _gate(self, context: ContextState, report: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        task = context.current_task
        workflow_id = context.workflow_id

        existing = None
        try:
            from repositories.approvals import approvals

            existing = await approvals.find_one(workflow_id=workflow_id, task_id=task.task_id)
        except Exception as exc:  # noqa: BLE001
            self.logger.error("Failed to look up existing approval.", context={"error": str(exc)})

        if existing:
            status = existing.get("status")
            if status == "approved":
                return {
                    "status": "success",
                    "approved": True,
                    "approval_id": existing.get("id"),
                    "reviewer": existing.get("approver_email"),
                }
            if status == "rejected":
                return {
                    "status": "failed",
                    "approved": False,
                    "approval_id": existing.get("id"),
                    "error": "Approval was rejected.",
                }
            # still pending
            return {"status": "pending_approval", "approved": False, "approval_id": existing.get("id")}

        employee_dict = context.employee.model_dump()
        try:
            from core.llm.service import LLMService

            reason = await LLMService.draft_approval_reason(employee_dict, report or {})
        except Exception as exc:  # noqa: BLE001 - LLM failures must never block the gate
            self.logger.error("Failed to draft approval reason.", context={"error": str(exc)})
            reason = "Manual review requested; automatic reasoning unavailable."

        try:
            from services.approvals import ApprovalService

            approval = await ApprovalService.request(
                workflow_id=workflow_id,
                task_id=task.task_id,
                title=task.name or "Approval required",
                description=getattr(task, "description", "") or "",
                reason=reason,
                employee_id=context.employee.id,
                required_role=(task.input_data or {}).get("approval_role", "hr"),
                payload={"verification_report": report},
            )
            approval_id = approval.get("id") if isinstance(approval, dict) else approval
        except Exception as exc:  # noqa: BLE001 - never let approval creation crash the workflow
            self.logger.error("Failed to create approval request.", context={"error": str(exc)})
            approval_id = None

        return {"status": "pending_approval", "approved": False, "approval_id": approval_id}

    # ------------------------------------------------------------------
    # Scheduler helpers
    # ------------------------------------------------------------------
    @staticmethod
    async def send_reminders() -> None:
        """Send reminders for every approval still pending past its reminder interval."""
        try:
            from repositories.approvals import approvals
            from services.approvals import ApprovalService

            pending = await approvals.list(status="pending")
            for approval in pending:
                await ApprovalService.send_reminder(approval)
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to send approval reminders.", context={"error": str(exc)})

    @staticmethod
    async def escalate_overdue() -> None:
        """Escalate every approval that has blown past its expiry."""
        try:
            from repositories.approvals import approvals
            from services.approvals import ApprovalService

            pending = await approvals.list(status="pending")
            for approval in pending:
                await ApprovalService.escalate(approval)
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to escalate overdue approvals.", context={"error": str(exc)})

    async def recover(self, context: ContextState, error: Exception) -> Dict[str, Any]:
        self.logger.error("Manager Agent encountered a fault.", exc_info=error)
        return {"status": "failed", "error": str(error)}
