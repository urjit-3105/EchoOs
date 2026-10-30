import asyncio
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from config.settings import settings
from core.state.models import ExecutionPlanState, TaskPlanState, ContextState, TaskState
from core.orchestrator.registry import AgentRegistry
from core.orchestrator.events import OrchestratorEventDispatcher, OrchestratorEvents
from core.orchestrator.retry import RetryManager
from core.logger.structured import get_logger

logger = get_logger(__name__)

# Statuses that satisfy a downstream dependency - a skipped task is a
# resolved branch, not a blocker, so dependents must still be able to run.
_RESOLVED_STATUSES = ("completed", "skipped")


class ExecutionManager:
    """
    Manages the parallel execution of tasks by dispatching them to the Agent Registry.
    """

    @staticmethod
    async def get_ready_tasks(plan: ExecutionPlanState) -> List[TaskPlanState]:
        """
        Determines which tasks are ready to execute based on dependency resolution.
        """
        ready_tasks = []
        for task in plan.tasks.values():
            if task.status == "pending" or task.status == "scheduled":
                # Check if all dependencies are completed (or skipped, which also
                # resolves the branch without producing output).
                can_run = True
                for dep_id in task.dependencies:
                    dep_task = plan.tasks.get(dep_id)
                    if not dep_task or dep_task.status not in _RESOLVED_STATUSES:
                        can_run = False
                        break

                if can_run:
                    ready_tasks.append(task)
        return ready_tasks

    @staticmethod
    async def execute_batch(workflow_id: str, tasks: List[TaskPlanState], context: ContextState, plan: ExecutionPlanState) -> None:
        """
        Executes a batch of independent tasks in parallel.
        """
        if not tasks:
            return

        logger.info(f"Executing batch of {len(tasks)} parallel tasks.", context={"workflow_id": workflow_id})

        # Dispatch ready events
        for task in tasks:
            await OrchestratorEventDispatcher.dispatch(OrchestratorEvents.TASK_READY, workflow_id, {"task_id": task.task_id})

        # Create execution coroutines
        coroutines = [ExecutionManager._execute_single_task(workflow_id, task, context, plan) for task in tasks]

        # Execute concurrently
        await asyncio.gather(*coroutines)

        await ExecutionManager._update_workflow_progress(workflow_id, plan)

    @staticmethod
    async def _execute_single_task(workflow_id: str, task: TaskPlanState, context: ContextState, plan: ExecutionPlanState) -> None:
        """
        Handles the lifecycle of a single task execution.
        """
        task.status = "active"
        task.started_at = datetime.utcnow()
        await OrchestratorEventDispatcher.dispatch(OrchestratorEvents.TASK_STARTED, workflow_id, {"task_id": task.task_id})

        await ExecutionManager._upsert_task_row(workflow_id, task)
        execution_row_id = await ExecutionManager._create_agent_execution_row(workflow_id, task)

        start_time = time.time()

        try:
            agent_name = task.assigned_agent or "ExecutionAgent"  # Fallback to a default agent
            agent = AgentRegistry.get_agent(agent_name)

            # Build a fresh, localized task context so the agent sees this
            # task's own tool/input, not whatever the previous task left behind.
            merged_input: Dict[str, Any] = dict(task.input_data or {})
            merged_input.setdefault("approval_condition", task.approval_condition)
            merged_input.setdefault("approval_role", task.approval_role)

            context.current_task = TaskState(
                task_id=task.task_id,
                name=task.name,
                assigned_agent=task.assigned_agent,
                tool_name=task.tool_name,
                input_data=merged_input,
            )

            # Execute Agent
            result = await agent.run(context)
            duration = time.time() - start_time
            status = result.get("status")

            if status == "pending_approval":
                # Human gate: pause this branch, do NOT treat it as a failure.
                task.status = "awaiting_approval"
                plan.status = "paused"
                await ExecutionManager._upsert_task_row(workflow_id, task, output=result)
                await ExecutionManager._finish_agent_execution_row(
                    execution_row_id, status="pending_approval", output=result, duration=duration
                )
                await ExecutionManager._set_workflow_status(workflow_id, "paused")
                await OrchestratorEventDispatcher.dispatch(
                    OrchestratorEvents.APPROVAL_REQUESTED,
                    workflow_id,
                    {"task_id": task.task_id, "approval_id": result.get("approval_id")},
                )
                return

            if status == "success":
                task.status = "completed"
                task.completed_at = datetime.utcnow()
                task.output_data = result
                task.error = None
                # Store output data in context for downstream tasks
                context.completed_tasks_results[task.task_id] = result
                await ExecutionManager._upsert_task_row(workflow_id, task, output=result)
                await ExecutionManager._finish_agent_execution_row(
                    execution_row_id, status="success", output=result, duration=duration
                )
                await OrchestratorEventDispatcher.dispatch(
                    OrchestratorEvents.TASK_COMPLETED, workflow_id, {"task_id": task.task_id, "result": result}
                )
            else:
                raise Exception(result.get("error", "Unknown execution error"))

        except Exception as e:
            duration = time.time() - start_time
            await ExecutionManager._finish_agent_execution_row(
                execution_row_id, status="failed", duration=duration, error=str(e)
            )
            await ExecutionManager._handle_task_failure(workflow_id, task, context, plan, str(e))

    # ------------------------------------------------------------------
    # Failure handling - honours the task's declared `on_failure` policy
    # ------------------------------------------------------------------
    @staticmethod
    async def _handle_task_failure(
        workflow_id: str, task: TaskPlanState, context: ContextState, plan: ExecutionPlanState, error_msg: str
    ) -> None:
        task.error = error_msg
        on_failure = task.on_failure or "retry"

        if on_failure == "skip":
            task.status = "skipped"
            await ExecutionManager._upsert_task_row(workflow_id, task, error=error_msg)
            logger.warning(f"Task {task.task_id} skipped after failure.", context={"workflow_id": workflow_id})
            return

        if on_failure == "fail_workflow":
            task.status = "failed"
            plan.status = "failed"
            await ExecutionManager._upsert_task_row(workflow_id, task, error=error_msg)
            await ExecutionManager._set_workflow_status(workflow_id, "failed", error_message=error_msg)
            await OrchestratorEventDispatcher.dispatch(
                OrchestratorEvents.TASK_FAILED, workflow_id, {"task_id": task.task_id, "error": error_msg}
            )
            await OrchestratorEventDispatcher.dispatch(OrchestratorEvents.WORKFLOW_FAILED, workflow_id)
            return

        if on_failure == "escalate":
            task.status = "awaiting_approval"
            plan.status = "paused"
            await ExecutionManager._escalate(workflow_id, task, context, error_msg)
            await ExecutionManager._upsert_task_row(workflow_id, task, error=error_msg)
            await ExecutionManager._set_workflow_status(workflow_id, "paused")
            await OrchestratorEventDispatcher.dispatch(
                OrchestratorEvents.TASK_FAILED, workflow_id, {"task_id": task.task_id, "error": error_msg}
            )
            return

        # Default: "retry"
        action = await RetryManager.handle_failure(workflow_id, task, error_msg)
        if action == "retry":
            delay = settings.retry_backoff_factor ** max(task.retry_policy.attempts, 1)
            await asyncio.sleep(delay)
            task.status = "scheduled"  # Put back in queue
            await ExecutionManager._upsert_task_row(workflow_id, task, error=error_msg)
        else:
            # Retries exhausted - escalate to a human rather than silently failing.
            task.status = "awaiting_approval"
            plan.status = "paused"
            await ExecutionManager._escalate(workflow_id, task, context, error_msg)
            await ExecutionManager._upsert_task_row(workflow_id, task, error=error_msg)
            await ExecutionManager._set_workflow_status(workflow_id, "paused")
            await OrchestratorEventDispatcher.dispatch(
                OrchestratorEvents.TASK_FAILED, workflow_id, {"task_id": task.task_id, "error": error_msg}
            )

    @staticmethod
    async def _escalate(workflow_id: str, task: TaskPlanState, context: ContextState, error_msg: str) -> Optional[str]:
        """Raise a human approval request for a task that cannot recover on its own."""
        try:
            from services.approvals import ApprovalService

            employee_id = context.employee.id if context.employee else None
            approval = await ApprovalService.request(
                workflow_id=workflow_id,
                task_id=task.task_id,
                title=f"Task failed: {task.name}",
                description=error_msg,
                reason="Task failed and requires manual intervention.",
                employee_id=employee_id,
                required_role=task.approval_role or "hr",
            )
            return approval.get("id") if isinstance(approval, dict) else approval
        except Exception as exc:  # noqa: BLE001 - escalation must never crash task handling
            logger.error("Failed to escalate failed task.", context={"task_id": task.task_id, "error": str(exc)})
            return None

    # ------------------------------------------------------------------
    # Persistence helpers - best effort, logged, never fatal
    # ------------------------------------------------------------------
    @staticmethod
    async def _upsert_task_row(
        workflow_id: str, task: TaskPlanState, *, output: Optional[Dict[str, Any]] = None, error: Optional[str] = None
    ) -> None:
        """Write/refresh the matching ``tasks`` row via the repository's own upsert helper.

        ``TaskRepository.upsert_from_plan`` covers the planner-derived fields
        (name, agent, tool, status, dependencies, priority, requires_approval);
        anything execution-time only (result/error/timestamps/retry count) is
        applied with a follow-up ``update`` against the same row.
        """
        try:
            from repositories.tasks import tasks as tasks_repo

            row = await tasks_repo.upsert_from_plan(workflow_id, task.model_dump())

            extra: Dict[str, Any] = {"retries": task.retry_policy.attempts, "input_data": task.input_data}
            if output is not None:
                extra["result"] = output
            if error is not None:
                extra["error_message"] = error
            if task.started_at:
                extra["started_at"] = task.started_at
            if task.completed_at:
                extra["completed_at"] = task.completed_at

            if row:
                await tasks_repo.update(row["id"], extra)
        except Exception as exc:  # noqa: BLE001 - persistence must never break the run
            logger.error("Failed to upsert task row.", context={"task_id": task.task_id, "error": str(exc)})

    @staticmethod
    async def _create_agent_execution_row(workflow_id: str, task: TaskPlanState) -> Optional[str]:
        try:
            from repositories.agent_executions import agent_executions

            row = await agent_executions.create(
                {
                    "workflow_id": workflow_id,
                    "task_id": task.task_id,
                    "agent_name": task.assigned_agent or "ExecutionAgent",
                    "action": task.tool_name or task.name,
                    "status": "running",
                    "input_data": task.input_data,
                    "attempt": task.retry_policy.attempts + 1,
                }
            )
            return row.get("id") if row else None
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to create agent_execution row.", context={"task_id": task.task_id, "error": str(exc)})
            return None

    @staticmethod
    async def _finish_agent_execution_row(
        execution_id: Optional[str],
        *,
        status: str,
        output: Optional[Dict[str, Any]] = None,
        duration: float = 0.0,
        error: Optional[str] = None,
    ) -> None:
        if not execution_id:
            return
        try:
            from repositories.agent_executions import agent_executions

            payload: Dict[str, Any] = {
                "status": status,
                "duration_seconds": duration,
                "completed_at": datetime.utcnow(),
            }
            if output is not None:
                payload["output_data"] = output
            if error is not None:
                payload["error_message"] = error
            await agent_executions.update(execution_id, payload)
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to finalize agent_execution row.", context={"error": str(exc)})

    @staticmethod
    async def _set_workflow_status(workflow_id: str, status: str, *, error_message: Optional[str] = None) -> None:
        try:
            from repositories.workflows import workflows as workflows_repo

            payload: Dict[str, Any] = {"status": status}
            if error_message:
                payload["error_message"] = error_message
            await workflows_repo.update(workflow_id, payload)
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to update workflow status.", context={"workflow_id": workflow_id, "error": str(exc)})

    @staticmethod
    async def _update_workflow_progress(workflow_id: str, plan: ExecutionPlanState) -> None:
        """Recompute progress% and current_stage after a batch finishes."""
        total = len(plan.tasks)
        if total == 0:
            return
        completed = sum(1 for t in plan.tasks.values() if t.status in _RESOLVED_STATUSES)
        progress = int((completed / total) * 100)

        running_tasks = [t for t in plan.tasks.values() if t.status == "active"]
        current_stage = None
        if running_tasks:
            newest = max(running_tasks, key=lambda t: t.started_at or datetime.min)
            current_stage = newest.stage

        try:
            from repositories.workflows import workflows as workflows_repo

            payload: Dict[str, Any] = {"progress": progress}
            if current_stage:
                payload["current_stage"] = current_stage
            await workflows_repo.update(workflow_id, payload)
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to update workflow progress.", context={"workflow_id": workflow_id, "error": str(exc)})
