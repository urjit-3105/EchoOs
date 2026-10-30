import asyncio
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from core.state.models import ContextState, ExecutionPlanState
from core.orchestrator.runtime import WorkflowRuntime
from core.orchestrator.events import OrchestratorEventDispatcher, OrchestratorEvents
from core.orchestrator.approval import ApprovalManager
from core.logger.structured import get_logger

logger = get_logger(__name__)


class OrchestratorService:
    """
    High-level API service for managing workflows in the Multi-Agent Orchestrator.

    ``_active_plans``/``_active_contexts`` remain an in-memory hot cache for the
    common case (same process, workflow still running), but every state change
    is now also persisted so a restart - or a request that lands on a different
    worker - can rehydrate the plan from the database instead of losing it.
    """

    # Hot cache. Source of truth is ``execution_plans`` in the database.
    _active_plans: Dict[str, ExecutionPlanState] = {}
    _active_contexts: Dict[str, ContextState] = {}

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    @classmethod
    async def start_workflow(cls, plan: ExecutionPlanState, context: ContextState) -> str:
        """Starts a new workflow execution."""
        workflow_id = plan.workflow_id
        cls._active_plans[workflow_id] = plan
        cls._active_contexts[workflow_id] = context

        logger.info(f"Orchestrator Service starting workflow {workflow_id}")

        await cls._persist(plan)
        await cls._set_workflow_row(workflow_id, {"status": "running", "started_at": datetime.utcnow().isoformat()})

        # We start the runtime asynchronously so it doesn't block the API
        asyncio.create_task(WorkflowRuntime.run(workflow_id, plan, context))

        return workflow_id

    @classmethod
    async def pause_workflow(cls, workflow_id: str) -> bool:
        """Pauses a running workflow. The in-flight batch finishes; no new batch is dispatched."""
        plan, _context = await cls._resolve(workflow_id)
        if not plan:
            raise ValueError(f"Workflow {workflow_id} not found.")

        plan.status = "paused"
        await cls._persist(plan)
        await cls._set_workflow_row(workflow_id, {"status": "paused"})
        await OrchestratorEventDispatcher.dispatch(OrchestratorEvents.WORKFLOW_PAUSED, workflow_id)
        return True

    @classmethod
    async def resume_workflow(cls, workflow_id: str, action: str, details: Dict[str, Any] = None) -> bool:
        """
        Resumes a paused workflow.

        ``action`` is one of:
          - ``"approve"``: completes the approval-gated task named in ``details['task_id']``.
          - ``"reject"``: fails the workflow at that task.
          - ``"resume"``: plain unpause (no pending approval to resolve).
        """
        details = details or {}
        plan, context = await cls._resolve(workflow_id)
        if not plan or not context:
            raise ValueError(f"Workflow {workflow_id} not found.")

        if action == "approve":
            task_id = details.get("task_id")
            if not task_id or task_id not in plan.tasks:
                return False
            task = plan.tasks[task_id]
            await ApprovalManager.process_approval(workflow_id, task, approved=True, reviewer=details.get("reviewer"))
            task.status = "completed"
            task.error = None

        elif action == "reject":
            task_id = details.get("task_id")
            if not task_id or task_id not in plan.tasks:
                return False
            task = plan.tasks[task_id]
            await ApprovalManager.process_approval(workflow_id, task, approved=False, reviewer=details.get("reviewer"))
            task.status = "failed"
            task.error = details.get("reason", "Rejected by reviewer.")
            plan.status = "failed"
            await cls._persist(plan)
            await cls._set_workflow_row(workflow_id, {"status": "failed", "error_message": task.error})
            await OrchestratorEventDispatcher.dispatch(OrchestratorEvents.WORKFLOW_FAILED, workflow_id)
            return True

        elif action == "resume":
            pass  # plain unpause - nothing task-specific to resolve

        else:
            return False

        if plan.status == "paused":
            plan.status = "running"
        await cls._persist(plan)
        await cls._set_workflow_row(workflow_id, {"status": "running"})

        asyncio.create_task(WorkflowRuntime.run(workflow_id, plan, context))
        return True

    @classmethod
    async def cancel_workflow(cls, workflow_id: str) -> bool:
        """Cancels a running workflow."""
        plan, _context = await cls._resolve(workflow_id)
        if not plan:
            raise ValueError(f"Workflow {workflow_id} not found.")

        plan.status = "cancelled"
        await cls._persist(plan)
        await cls._set_workflow_row(workflow_id, {"status": "cancelled"})

        await OrchestratorEventDispatcher.dispatch(OrchestratorEvents.WORKFLOW_CANCELLED, workflow_id)
        logger.warning(f"Workflow {workflow_id} cancelled via OrchestratorService.")
        return True

    @classmethod
    async def get_status(cls, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Returns the current state of the execution plan, hydrating from the database on a cache miss."""
        plan = cls._active_plans.get(workflow_id)
        if plan:
            return plan.model_dump()

        plan, _context = await cls._resolve(workflow_id)
        return plan.model_dump() if plan else None

    @classmethod
    async def retry_task(cls, workflow_id: str, task_id: str) -> bool:
        """Resets a single failed/awaiting task to pending and re-enters the runtime."""
        plan, context = await cls._resolve(workflow_id)
        if not plan or not context:
            raise ValueError(f"Workflow {workflow_id} not found.")
        if task_id not in plan.tasks:
            raise ValueError(f"Task {task_id} not found in workflow {workflow_id}.")

        task = plan.tasks[task_id]
        task.status = "pending"
        task.error = None
        task.retry_policy.attempts = 0

        if plan.status in ("failed", "paused"):
            plan.status = "running"

        await cls._persist(plan)
        await cls._set_workflow_row(workflow_id, {"status": "running"})

        asyncio.create_task(WorkflowRuntime.run(workflow_id, plan, context))
        return True

    @classmethod
    async def retry_workflow(cls, workflow_id: str) -> bool:
        """Resets every failed/awaiting-approval task to pending and re-enters the runtime."""
        plan, context = await cls._resolve(workflow_id)
        if not plan or not context:
            raise ValueError(f"Workflow {workflow_id} not found.")

        for task in plan.tasks.values():
            if task.status in ("failed", "awaiting_approval"):
                task.status = "pending"
                task.error = None
                task.retry_policy.attempts = 0

        plan.status = "running"
        await cls._persist(plan)
        await cls._set_workflow_row(workflow_id, {"status": "running"})

        asyncio.create_task(WorkflowRuntime.run(workflow_id, plan, context))
        return True

    # ------------------------------------------------------------------
    # Persistence / hydration
    # ------------------------------------------------------------------
    @classmethod
    async def _resolve(cls, workflow_id: str) -> Tuple[Optional[ExecutionPlanState], Optional[ContextState]]:
        """Cache hit, or fall through to `_hydrate` to rebuild from the database."""
        if workflow_id in cls._active_plans and workflow_id in cls._active_contexts:
            return cls._active_plans[workflow_id], cls._active_contexts[workflow_id]
        return await cls._hydrate(workflow_id)

    @classmethod
    async def _persist(cls, plan: ExecutionPlanState) -> None:
        """Upserts the serialized plan into ``execution_plans`` after every state change.

        The first write for a workflow goes through ``save_plan`` (the
        repository's own helper for a freshly generated plan); every
        subsequent state change updates that same row instead of appending a
        new one.
        """
        try:
            from repositories.execution_plans import execution_plans

            plan_dict = plan.model_dump()
            existing = await execution_plans.get_latest(plan.workflow_id)
            if existing:
                await execution_plans.update(
                    existing["id"],
                    {
                        "plan_data": plan_dict,
                        "critical_path": plan.critical_path,
                        "estimated_duration": plan.estimated_total_duration,
                        "status": plan.status,
                    },
                )
            else:
                await execution_plans.save_plan(plan.workflow_id, plan_dict)
        except Exception as exc:  # noqa: BLE001 - persistence must never break the API call
            logger.error("Failed to persist execution plan.", context={"workflow_id": plan.workflow_id, "error": str(exc)})

    @classmethod
    async def _hydrate(cls, workflow_id: str) -> Tuple[Optional[ExecutionPlanState], Optional[ContextState]]:
        """Rebuilds ``plan``/``context`` from the database - used after a restart or on another worker."""
        try:
            from repositories.execution_plans import execution_plans

            row = await execution_plans.get_latest(workflow_id)
            if not row or not row.get("plan_data"):
                return None, None
            plan = ExecutionPlanState(**row["plan_data"])
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to hydrate execution plan.", context={"workflow_id": workflow_id, "error": str(exc)})
            return None, None

        context = await cls._rebuild_context(workflow_id, plan)
        if context is None:
            return None, None

        cls._active_plans[workflow_id] = plan
        cls._active_contexts[workflow_id] = context
        return plan, context

    @classmethod
    async def _rebuild_context(cls, workflow_id: str, plan: ExecutionPlanState) -> Optional[ContextState]:
        """Reconstructs a usable ``ContextState`` from the persisted workflow row."""
        try:
            from repositories.workflows import workflows as workflows_repo
            from repositories.employees import employees as employees_repo
            from core.state.models import EmployeeState, TaskState

            workflow_row = await workflows_repo.get(workflow_id)
            if not workflow_row:
                return None

            employee_row = None
            employee_id = workflow_row.get("employee_id")
            if employee_id:
                employee_row = await employees_repo.get(employee_id)

            employee_state = EmployeeState(
                id=employee_id or (employee_row or {}).get("id", ""),
                first_name=(employee_row or {}).get("first_name", ""),
                last_name=(employee_row or {}).get("last_name", ""),
                email=(employee_row or {}).get("email", ""),
                department=(employee_row or {}).get("department"),
                role=(employee_row or {}).get("role"),
            )

            stored_context = workflow_row.get("context") or {}

            return ContextState(
                workflow_id=workflow_id,
                employee=employee_state,
                current_task=TaskState(task_id="hydrated", name="hydrated"),
                workflow_definition=stored_context.get("workflow_definition", {}),
                configuration=stored_context.get("configuration", {}),
                global_variables=stored_context.get("global_variables", {}),
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to rebuild context for hydration.", context={"workflow_id": workflow_id, "error": str(exc)})
            return None

    @classmethod
    async def _set_workflow_row(cls, workflow_id: str, payload: Dict[str, Any]) -> None:
        try:
            from repositories.workflows import workflows as workflows_repo

            await workflows_repo.update(workflow_id, payload)
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to update workflow row.", context={"workflow_id": workflow_id, "error": str(exc)})
