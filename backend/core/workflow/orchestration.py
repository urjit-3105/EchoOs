"""High-level onboarding entry point.

``OnboardingOrchestrator`` is the seam between the HTTP/service layer and the
low-level orchestrator primitives (``PlannerAgent`` -> ``OrchestratorService``
-> ``WorkflowRuntime``). Routes and background jobs should call this class,
not ``OrchestratorService`` directly, so plan generation, persistence and
notifications always happen together.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from core.logger.structured import get_logger

logger = get_logger(__name__)


class OnboardingOrchestrator:
    """Coordinates starting, inspecting and controlling an employee's onboarding workflow."""

    # ------------------------------------------------------------------
    # Start
    # ------------------------------------------------------------------
    @staticmethod
    async def start_for_employee(employee_id: str, template_key: Optional[str] = None) -> Dict[str, Any]:
        """Creates the workflow row, plans it, and hands it to the orchestrator."""
        from config.settings import settings
        from core.orchestrator.registry import AgentRegistry
        from core.orchestrator.service import OrchestratorService
        from core.state.models import ContextState, EmployeeState, ExecutionPlanState, TaskState
        from core.workflow.templates import WorkflowTemplateRegistry
        from repositories.employees import employees as employees_repo
        from repositories.organizations import organizations as organizations_repo
        from repositories.tasks import tasks as tasks_repo
        from repositories.workflows import workflows as workflows_repo

        employee_row = await employees_repo.get(employee_id)
        if not employee_row:
            raise ValueError(f"Employee {employee_id} not found.")

        organization_row: Optional[Dict[str, Any]] = None
        if employee_row.get("organization_id"):
            organization_row = await organizations_repo.get(employee_row["organization_id"])

        template_key = template_key or settings.default_workflow_template
        template = WorkflowTemplateRegistry.get(template_key)

        workflow_row = await workflows_repo.create(
            {
                "organization_id": employee_row.get("organization_id"),
                "employee_id": employee_id,
                "template_id": template_key,
                "name": template.get("name", template_key),
                "status": "pending",
            }
        )
        workflow_id = workflow_row["id"]

        employee_state = EmployeeState(
            id=employee_id,
            first_name=employee_row.get("first_name", ""),
            last_name=employee_row.get("last_name", ""),
            email=employee_row.get("email", ""),
            department=employee_row.get("department"),
            role=employee_row.get("role"),
        )

        documents: List[Dict[str, Any]] = []
        try:
            from repositories.documents import documents as documents_repo

            documents = await documents_repo.list(employee_id=employee_id)
        except Exception as exc:  # noqa: BLE001 - documents are optional context, never fatal
            logger.error("Failed to load employee documents.", context={"error": str(exc)})

        global_variables = {
            "documents": documents,
            "organization": organization_row or {},
            "employee_record": employee_row,
        }
        configuration = {
            "max_retries": settings.max_retries,
            "retry_backoff_factor": settings.retry_backoff_factor,
            "escalation_timeout_seconds": settings.escalation_timeout_seconds,
            "require_manager_approval": settings.require_manager_approval,
        }

        context = ContextState(
            workflow_id=workflow_id,
            employee=employee_state,
            current_task=TaskState(task_id="planning", name="Generate Execution Plan"),
            configuration=configuration,
            workflow_definition=template,
            global_variables=global_variables,
        )

        # Persist enough of the context on the workflow row itself so
        # OrchestratorService._rebuild_context can rehydrate after a restart.
        try:
            await workflows_repo.update(
                workflow_id,
                {
                    "context": {
                        "workflow_definition": template,
                        "configuration": configuration,
                        "global_variables": global_variables,
                    }
                },
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to persist workflow context.", context={"workflow_id": workflow_id, "error": str(exc)})

        planner_agent = AgentRegistry.get_agent("PlannerAgent")
        plan_result = await planner_agent.run(context)
        if plan_result.get("status") != "success":
            error_message = str(plan_result.get("message") or plan_result.get("error") or plan_result)
            await workflows_repo.update(workflow_id, {"status": "failed", "error_message": error_message})
            raise ValueError(f"Planning failed for workflow {workflow_id}: {error_message}")

        plan = ExecutionPlanState(**plan_result["plan"])

        # Write the tasks rows up front so task/status endpoints see the full
        # plan immediately, before the first batch even starts executing.
        for task in plan.tasks.values():
            try:
                await tasks_repo.upsert_from_plan(workflow_id, task.model_dump())
            except Exception as exc:  # noqa: BLE001 - one bad row shouldn't stop the whole plan
                logger.error("Failed to write task row.", context={"task_id": task.task_id, "error": str(exc)})

        await OrchestratorService.start_workflow(plan, context)

        try:
            from services.audit import AuditService

            await AuditService.record(
                action="workflow.started",
                resource_type="workflow",
                resource_id=workflow_id,
                actor="Onboarding Orchestrator",
                actor_type="system",
                organization_id=employee_row.get("organization_id"),
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to record audit log.", context={"error": str(exc)})

        try:
            from services.notifications import NotificationService

            await NotificationService.push(
                type="info",
                title="Onboarding started",
                message=f"Onboarding started for {employee_state.first_name} {employee_state.last_name}.",
                category="workflow",
                organization_id=employee_row.get("organization_id"),
                employee_id=employee_id,
                workflow_id=workflow_id,
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to push start notification.", context={"error": str(exc)})

        try:
            from core.events.bus import EventBus

            await EventBus.publish("WorkflowStarted", {"workflow_id": workflow_id, "employee_id": employee_id})
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to publish WorkflowStarted event.", context={"error": str(exc)})

        refreshed = await workflows_repo.get(workflow_id)
        return refreshed or workflow_row

    # ------------------------------------------------------------------
    # Read model
    # ------------------------------------------------------------------
    @staticmethod
    async def status(workflow_id: str) -> Dict[str, Any]:
        """Workflow row + tasks + latest verification report + pending approvals, shaped for the UI."""
        from repositories.tasks import tasks as tasks_repo
        from repositories.workflows import workflows as workflows_repo

        workflow_row = await workflows_repo.get(workflow_id)
        if not workflow_row:
            raise ValueError(f"Workflow {workflow_id} not found.")

        task_rows = await tasks_repo.list(workflow_id=workflow_id)

        latest_report = None
        try:
            from repositories.verification_reports import verification_reports

            rows = await verification_reports.list(
                workflow_id=workflow_id, order_by="created_at", descending=True, limit=1
            )
            latest_report = rows[0] if rows else None
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to load verification report.", context={"error": str(exc)})

        pending_approvals: List[Dict[str, Any]] = []
        try:
            from repositories.approvals import approvals

            pending_approvals = await approvals.list(workflow_id=workflow_id, status="pending")
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to load pending approvals.", context={"error": str(exc)})

        recent_logs: List[Dict[str, Any]] = []
        try:
            from repositories.execution_logs import execution_logs

            recent_logs = await execution_logs.list(
                workflow_id=workflow_id, order_by="timestamp", descending=True, limit=20
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to load execution logs.", context={"error": str(exc)})

        return {
            "workflow": workflow_row,
            "tasks": task_rows,
            "verification_report": latest_report,
            "pending_approvals": pending_approvals,
            "recent_logs": recent_logs,
        }

    @staticmethod
    async def history(workflow_id: str) -> List[Dict[str, Any]]:
        """Merged, time-sorted execution_logs + agent_executions + audit_logs for the timeline view."""
        entries: List[Dict[str, Any]] = []

        try:
            from repositories.execution_logs import execution_logs

            for row in await execution_logs.list(workflow_id=workflow_id):
                entries.append({"source": "execution_log", "timestamp": row.get("timestamp"), **row})
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to load execution_logs for history.", context={"error": str(exc)})

        try:
            from repositories.agent_executions import agent_executions

            for row in await agent_executions.list(workflow_id=workflow_id):
                entries.append({"source": "agent_execution", "timestamp": row.get("started_at"), **row})
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to load agent_executions for history.", context={"error": str(exc)})

        try:
            from repositories.audit import audit_logs

            for row in await audit_logs.list(resource_type="workflow", resource_id=workflow_id):
                entries.append({"source": "audit_log", "timestamp": row.get("timestamp"), **row})
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to load audit_logs for history.", context={"error": str(exc)})

        entries.sort(key=lambda entry: entry.get("timestamp") or "")
        return entries

    # ------------------------------------------------------------------
    # Control - thin delegation to OrchestratorService
    # ------------------------------------------------------------------
    @staticmethod
    async def pause(workflow_id: str) -> bool:
        from core.orchestrator.service import OrchestratorService

        return await OrchestratorService.pause_workflow(workflow_id)

    @staticmethod
    async def resume(workflow_id: str, action: str = "resume", details: Optional[Dict[str, Any]] = None) -> bool:
        from core.orchestrator.service import OrchestratorService

        return await OrchestratorService.resume_workflow(workflow_id, action, details or {})

    @staticmethod
    async def cancel(workflow_id: str) -> bool:
        from core.orchestrator.service import OrchestratorService

        return await OrchestratorService.cancel_workflow(workflow_id)

    @staticmethod
    async def retry(workflow_id: str, task_id: Optional[str] = None) -> bool:
        from core.orchestrator.service import OrchestratorService

        if task_id:
            return await OrchestratorService.retry_task(workflow_id, task_id)
        return await OrchestratorService.retry_workflow(workflow_id)

    # ------------------------------------------------------------------
    # Event handlers / background maintenance
    # ------------------------------------------------------------------
    @staticmethod
    async def on_approval_resolved(payload: Dict[str, Any]) -> None:
        """Handler for the ``"ApprovalResolved"`` event - resumes or fails the paused workflow.

        Intended to be wired up once at startup, e.g.
        ``EventBus.subscribe("ApprovalResolved", OnboardingOrchestrator.on_approval_resolved)``.
        """
        workflow_id = payload.get("workflow_id")
        if not workflow_id:
            logger.warning("ApprovalResolved event missing workflow_id.", context={"payload": payload})
            return

        from core.orchestrator.service import OrchestratorService

        task_id = payload.get("task_id")
        approved = bool(payload.get("approved"))
        reviewer = payload.get("approver_email") or payload.get("reviewer")

        try:
            if approved:
                await OrchestratorService.resume_workflow(
                    workflow_id, "approve", {"task_id": task_id, "reviewer": reviewer}
                )
            else:
                await OrchestratorService.resume_workflow(
                    workflow_id,
                    "reject",
                    {"task_id": task_id, "reviewer": reviewer, "reason": payload.get("comments")},
                )
        except Exception as exc:  # noqa: BLE001 - a bad event must not crash the event bus
            logger.error(
                "Failed to resume workflow after approval resolution.",
                context={"workflow_id": workflow_id, "error": str(exc)},
            )

    @staticmethod
    async def recover_stalled() -> None:
        """Finds ``running`` workflows with no recent task activity and re-enters the runtime.

        Meant to be called periodically by the background scheduler - protects
        against a process restart (or a crashed asyncio task) silently
        stranding a workflow mid-run.
        """
        from config.settings import settings
        from core.orchestrator.runtime import WorkflowRuntime
        from core.orchestrator.service import OrchestratorService

        try:
            from repositories.tasks import tasks as tasks_repo
            from repositories.workflows import workflows as workflows_repo

            running_rows = await workflows_repo.list(status="running")
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to list running workflows.", context={"error": str(exc)})
            return

        now = datetime.utcnow()

        for row in running_rows:
            workflow_id = row["id"]
            last_activity_str = row.get("started_at") or row.get("updated_at")

            try:
                task_rows = await tasks_repo.list(workflow_id=workflow_id, order_by="updated_at", descending=True, limit=1)
                if task_rows:
                    last_activity_str = task_rows[0].get("updated_at") or last_activity_str
            except Exception as exc:  # noqa: BLE001
                logger.error("Failed to load task activity.", context={"workflow_id": workflow_id, "error": str(exc)})

            if not last_activity_str:
                continue

            try:
                last_activity = datetime.fromisoformat(str(last_activity_str).replace("Z", ""))
            except ValueError:
                continue

            if (now - last_activity).total_seconds() <= settings.escalation_timeout_seconds:
                continue

            logger.warning("Workflow appears stalled; re-entering runtime.", context={"workflow_id": workflow_id})
            try:
                plan, context = await OrchestratorService._resolve(workflow_id)
                if plan and context and plan.status == "running":
                    import asyncio

                    asyncio.create_task(WorkflowRuntime.run(workflow_id, plan, context))
            except Exception as exc:  # noqa: BLE001 - one stuck workflow shouldn't block the sweep
                logger.error("Failed to recover stalled workflow.", context={"workflow_id": workflow_id, "error": str(exc)})


def _register_approval_handler() -> None:
    """Wires ``OnboardingOrchestrator.on_approval_resolved`` to the ``ApprovalResolved`` event.

    ``services.onboarding.OnboardingService.register_event_handlers`` (the
    app's general event-wiring entry point) only subscribes the two events
    that kick off onboarding - it deliberately leaves orchestration-internal
    events to this module. Runs once, the first time this module is imported.
    """
    try:
        from core.events.bus import EventBus

        EventBus.subscribe("ApprovalResolved", OnboardingOrchestrator.on_approval_resolved)
    except Exception as exc:  # noqa: BLE001 - must never block module import
        logger.error("Failed to subscribe ApprovalResolved handler.", context={"error": str(exc)})


_register_approval_handler()
