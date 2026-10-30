"""Task instances - list, inspect, retry, and per-task execution logs."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from core.logger.structured import get_logger
from core.workflow.orchestration import OnboardingOrchestrator
from repositories import execution_logs as execution_logs_repo
from repositories import tasks as tasks_repo

logger = get_logger(__name__)

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("/")
async def list_tasks(
    workflow_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
) -> List[Dict[str, Any]]:
    """List tasks, optionally filtered by workflow/status."""
    filters: Dict[str, Any] = {}
    if workflow_id:
        filters["workflow_id"] = workflow_id
    if status:
        filters["status"] = status
    return await tasks_repo.list(order_by="created_at", limit=limit, **filters)


@router.get("/{task_id}")
async def get_task(task_id: str) -> Dict[str, Any]:
    """Fetch a single task row."""
    task = await tasks_repo.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")
    return task


@router.post("/{task_id}/retry")
async def retry_task(task_id: str) -> Dict[str, Any]:
    """Retry a single task via the orchestrator."""
    task = await tasks_repo.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")

    try:
        success = await OnboardingOrchestrator.retry(task["workflow_id"], task.get("task_key") or task_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"message": f"Task '{task_id}' retry triggered.", "success": success}


@router.get("/{task_id}/logs")
async def get_task_logs(task_id: str) -> List[Dict[str, Any]]:
    """Execution logs recorded for this task."""
    task = await tasks_repo.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")
    logs = await execution_logs_repo.list_by_workflow(task["workflow_id"])
    return [log for log in logs if log.get("task_id") == task_id]
