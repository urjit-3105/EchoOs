"""Workflow lifecycle: templates, start/pause/resume/cancel/retry, status and history."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.logger.structured import get_logger
from core.workflow.orchestration import OnboardingOrchestrator
from core.workflow.templates import WorkflowTemplateRegistry
from repositories import execution_plans as execution_plans_repo
from repositories import tasks as tasks_repo
from repositories import workflow_templates as workflow_templates_repo
from repositories import workflows as workflows_repo
from services.onboarding import OnboardingService

logger = get_logger(__name__)

router = APIRouter(prefix="/workflow", tags=["Workflow"])


class WorkflowStartRequest(BaseModel):
    employee_id: str
    template_key: Optional[str] = None


class TemplateDefinitionRequest(BaseModel):
    key: str
    name: str
    description: Optional[str] = None
    definition: Dict[str, Any]


# ---------------------------------------------------------------------------
# Static paths first - /templates must be declared before /{workflow_id}
# ---------------------------------------------------------------------------
@router.get("/templates")
async def list_templates() -> List[Dict[str, Any]]:
    """Summaries of every registered workflow template."""
    return WorkflowTemplateRegistry.list()


@router.post("/templates")
async def register_template(payload: TemplateDefinitionRequest) -> Dict[str, Any]:
    """Register (or overwrite) a workflow template definition at runtime and persist it."""
    WorkflowTemplateRegistry.register(payload.key, payload.definition)
    row = await workflow_templates_repo.upsert_definition(
        payload.key, payload.name, payload.description, payload.definition
    )
    return row


@router.get("/templates/{key}")
async def get_template(key: str) -> Dict[str, Any]:
    """The full template definition, so the UI can draw the DAG."""
    try:
        return WorkflowTemplateRegistry.get(key)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/start")
async def start_workflow(payload: WorkflowStartRequest) -> Dict[str, Any]:
    """Start an onboarding workflow for an employee."""
    try:
        workflow = await OnboardingService.start(payload.employee_id, payload.template_key)
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"workflow": workflow}


@router.get("/")
async def list_workflows(
    organization_id: Optional[str] = None,
    employee_id: Optional[str] = None,
    status: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """List workflows with optional filters."""
    filters: Dict[str, Any] = {}
    if organization_id:
        filters["organization_id"] = organization_id
    if employee_id:
        filters["employee_id"] = employee_id
    if status:
        filters["status"] = status
    return await workflows_repo.list(order_by="created_at", descending=True, **filters)


@router.get("/{workflow_id}")
async def get_workflow(workflow_id: str) -> Dict[str, Any]:
    """Workflow row + tasks + latest verification report + pending approvals + recent logs."""
    try:
        return await OnboardingOrchestrator.status(workflow_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{workflow_id}/status")
async def get_workflow_status(workflow_id: str) -> Dict[str, Any]:
    """Live execution-plan status (from the in-memory/hydrated orchestrator state)."""
    from core.orchestrator.service import OrchestratorService

    status = await OrchestratorService.get_status(workflow_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found.")
    return status


@router.get("/{workflow_id}/tasks")
async def get_workflow_tasks(workflow_id: str) -> List[Dict[str, Any]]:
    """Task rows for a workflow."""
    return await tasks_repo.list_by_workflow(workflow_id)


@router.get("/{workflow_id}/history")
async def get_workflow_history(workflow_id: str) -> List[Dict[str, Any]]:
    """Merged, time-sorted execution/agent/audit history."""
    return await OnboardingOrchestrator.history(workflow_id)


@router.get("/{workflow_id}/plan")
async def get_workflow_plan(workflow_id: str) -> Dict[str, Any]:
    """The persisted execution plan, including the critical path and stages."""
    plan = await execution_plans_repo.get_latest(workflow_id)
    if not plan:
        raise HTTPException(status_code=404, detail=f"No execution plan found for workflow '{workflow_id}'.")
    return plan


@router.post("/{workflow_id}/pause")
async def pause_workflow(workflow_id: str) -> Dict[str, Any]:
    """Pause a running workflow."""
    try:
        success = await OnboardingOrchestrator.pause(workflow_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"message": "Workflow paused.", "success": success}


@router.post("/{workflow_id}/resume")
async def resume_workflow(workflow_id: str) -> Dict[str, Any]:
    """Resume a paused workflow."""
    try:
        success = await OnboardingOrchestrator.resume(workflow_id, "resume")
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"message": "Workflow resumed.", "success": success}


@router.post("/{workflow_id}/cancel")
async def cancel_workflow(workflow_id: str) -> Dict[str, Any]:
    """Cancel a workflow."""
    try:
        success = await OnboardingOrchestrator.cancel(workflow_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"message": "Workflow cancelled.", "success": success}


@router.post("/{workflow_id}/retry")
async def retry_workflow(workflow_id: str) -> Dict[str, Any]:
    """Retry every failed/awaiting-approval task in the workflow."""
    try:
        success = await OnboardingOrchestrator.retry(workflow_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"message": "Workflow retry triggered.", "success": success}


@router.post("/{workflow_id}/tasks/{task_id}/retry")
async def retry_workflow_task(workflow_id: str, task_id: str) -> Dict[str, Any]:
    """Retry a single task within a workflow."""
    try:
        success = await OnboardingOrchestrator.retry(workflow_id, task_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"message": f"Task '{task_id}' retry triggered.", "success": success}
