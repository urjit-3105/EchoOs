"""Real Monitoring Agent.

Watches the provisioning fan-out (and, at the end of a run, the whole
workflow), attempts one automatic recovery pass on recoverable failures, and
escalates anything still broken to a human instead of letting the workflow
silently stall.
"""

from datetime import datetime
from typing import Any, Dict, List

from core.agents.base import BaseAgent
from core.orchestrator.registry import AgentRegistry
from core.state.models import ContextState, TaskState
from core.logger.structured import get_logger

logger = get_logger(__name__)


@AgentRegistry.register("MonitoringAgent")
class MonitoringAgent(BaseAgent):
    """Health-checks sibling tasks and confirms final workflow completion."""

    def __init__(self):
        super().__init__(
            name="Monitoring Agent",
            capabilities=[
                "health_check",
                "failure_detection",
                "retry_orchestration",
                "escalation",
                "completion_confirmation",
            ],
        )

    async def validate(self, context: ContextState) -> bool:
        return True

    async def execute(self, context: ContextState) -> Dict[str, Any]:
        action = (context.current_task.input_data or {}).get("action", "health_check")

        if action == "health_check":
            return await self._health_check(context)
        if action == "confirm_completion":
            return await self._confirm_completion(context)
        return await self._generic_summary(context)

    # ------------------------------------------------------------------
    # health_check
    # ------------------------------------------------------------------
    async def _health_check(self, context: ContextState) -> Dict[str, Any]:
        workflow_id = context.workflow_id
        from repositories.tasks import tasks as tasks_repo

        sibling_rows = await tasks_repo.list(workflow_id=workflow_id)

        failed_rows = [r for r in sibling_rows if r.get("status") == "failed"]
        skipped_rows = [r for r in sibling_rows if r.get("status") == "skipped"]
        succeeded_rows = [r for r in sibling_rows if r.get("status") == "completed"]

        recovered: List[str] = []
        escalated: List[str] = []

        for row in failed_rows:
            recovered_ok = await self._attempt_recovery(context, row)
            if recovered_ok:
                recovered.append(row.get("task_key") or row.get("id"))
            else:
                await self._escalate_task(context, row)
                escalated.append(row.get("task_key") or row.get("id"))

        issues_found = len(failed_rows)
        healthy = len(escalated) == 0

        self.log_execution(
            "health_check_completed",
            {
                "workflow_id": workflow_id,
                "issues_found": issues_found,
                "recovered": recovered,
                "escalated": escalated,
                "succeeded": len(succeeded_rows),
                "skipped": len(skipped_rows),
            },
        )

        return {
            "status": "success",
            "healthy": healthy,
            "issues_found": issues_found,
            "recovered": recovered,
            "escalated": escalated,
        }

    async def _attempt_recovery(self, context: ContextState, task_row: Dict[str, Any]) -> bool:
        """One recovery pass: re-run the task's tool through the ExecutionPipeline."""
        tool_name = task_row.get("tool_name")
        if not tool_name:
            return False

        from core.execution.engine import ExecutionPipeline
        from repositories.tasks import tasks as tasks_repo

        task_state = TaskState(
            task_id=task_row.get("task_key") or task_row.get("id"),
            name=task_row.get("name", "task"),
            tool_name=tool_name,
            input_data=task_row.get("input_data") or {},
        )

        try:
            result = await ExecutionPipeline.run(task_state)
        except Exception as exc:  # noqa: BLE001 - a broken plugin must not kill the health check
            self.logger.error("Recovery attempt raised.", context={"task_id": task_state.task_id, "error": str(exc)})
            return False

        success = result.get("status") == "success"
        try:
            await tasks_repo.update(
                task_row["id"],
                {
                    "status": "completed" if success else "failed",
                    "result": result,
                    "error_message": None if success else result.get("error"),
                },
            )
        except Exception as exc:  # noqa: BLE001
            self.logger.error("Failed to persist recovery result.", context={"error": str(exc)})

        return success

    async def _escalate_task(self, context: ContextState, task_row: Dict[str, Any]) -> None:
        try:
            from services.approvals import ApprovalService

            await ApprovalService.request(
                workflow_id=context.workflow_id,
                task_id=task_row.get("task_key") or task_row.get("id"),
                title=f"Provisioning failure: {task_row.get('name', 'task')}",
                description=task_row.get("error_message") or "Task failed and could not be auto-recovered.",
                reason="Automatic recovery attempt failed; human intervention required.",
                employee_id=context.employee.id,
                required_role="hr",
                payload={"task": task_row},
            )
        except Exception as exc:  # noqa: BLE001 - escalation must never crash the health check
            self.logger.error("Failed to escalate task failure.", context={"error": str(exc)})

    # ------------------------------------------------------------------
    # confirm_completion
    # ------------------------------------------------------------------
    async def _confirm_completion(self, context: ContextState) -> Dict[str, Any]:
        workflow_id = context.workflow_id

        from repositories.tasks import tasks as tasks_repo

        sibling_rows = await tasks_repo.list(workflow_id=workflow_id)
        non_skipped = [r for r in sibling_rows if r.get("status") != "skipped"]
        all_completed = all(r.get("status") == "completed" for r in non_skipped) if non_skipped else True

        if not all_completed:
            self.logger.warning("Not all tasks are completed yet.", context={"workflow_id": workflow_id})
            return {"status": "success", "completed": False}

        now = datetime.utcnow()

        try:
            from repositories.workflows import workflows as workflows_repo

            await workflows_repo.update(
                workflow_id,
                {"status": "completed", "progress": 100, "completed_at": now.isoformat()},
            )
        except Exception as exc:  # noqa: BLE001
            self.logger.error("Failed to mark workflow completed.", context={"error": str(exc)})

        try:
            from repositories.employees import employees as employees_repo

            await employees_repo.update(
                context.employee.id,
                {"status": "active", "activated_at": now.isoformat()},
            )
        except Exception as exc:  # noqa: BLE001
            self.logger.error("Failed to activate employee.", context={"error": str(exc)})

        try:
            from services.notifications import NotificationService

            await NotificationService.push(
                type="success",
                title="Onboarding complete",
                message=f"{context.employee.first_name} {context.employee.last_name} has been fully onboarded.",
                category="workflow",
                employee_id=context.employee.id,
                workflow_id=workflow_id,
            )
        except Exception as exc:  # noqa: BLE001
            self.logger.error("Failed to push completion notification.", context={"error": str(exc)})

        try:
            from services.audit import AuditService

            await AuditService.record(
                action="workflow.completed",
                resource_type="workflow",
                resource_id=workflow_id,
                actor="Monitoring Agent",
                actor_type="agent",
            )
        except Exception as exc:  # noqa: BLE001
            self.logger.error("Failed to record audit log.", context={"error": str(exc)})

        try:
            from services.email import EmailService

            await EmailService.send(
                to=context.employee.email,
                subject="Welcome aboard - your onboarding is complete!",
                template="onboarding_complete",
                html=f"<p>Hi {context.employee.first_name}, your onboarding is now complete. Welcome to the team!</p>",
            )
        except Exception as exc:  # noqa: BLE001
            self.logger.error("Failed to send completion email.", context={"error": str(exc)})

        await self.emit_event("WorkflowCompleted", {"workflow_id": workflow_id, "employee_id": context.employee.id})

        return {"status": "success", "completed": True}

    # ------------------------------------------------------------------
    # default
    # ------------------------------------------------------------------
    async def _generic_summary(self, context: ContextState) -> Dict[str, Any]:
        workflow_id = context.workflow_id
        try:
            from repositories.tasks import tasks as tasks_repo

            rows = await tasks_repo.list(workflow_id=workflow_id)
        except Exception as exc:  # noqa: BLE001
            self.logger.error("Failed to load tasks for summary.", context={"error": str(exc)})
            rows = []

        statuses: Dict[str, int] = {}
        for row in rows:
            status = row.get("status", "unknown")
            statuses[status] = statuses.get(status, 0) + 1

        return {"status": "success", "summary": statuses, "total_tasks": len(rows)}

    async def recover(self, context: ContextState, error: Exception) -> Dict[str, Any]:
        self.logger.error("Monitoring Agent encountered a fault.", exc_info=error)
        try:
            from services.approvals import ApprovalService

            await ApprovalService.request(
                workflow_id=context.workflow_id,
                task_id=context.current_task.task_id,
                title="Monitoring Agent failure",
                description=str(error),
                reason="Monitoring Agent raised an unhandled exception.",
                employee_id=context.employee.id,
                required_role="hr",
            )
        except Exception as exc:  # noqa: BLE001
            self.logger.error("Failed to escalate Monitoring Agent failure.", context={"error": str(exc)})

        return {"status": "failed", "error": str(error)}
