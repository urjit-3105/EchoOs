"""System health, aggregate metrics and stalled-workflow recovery."""

from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter

from config.settings import settings
from core.execution.plugins import PLUGIN_CATALOG
from core.llm.service import LLMService
from core.logger.structured import get_logger
from core.orchestrator.registry import AgentRegistry
from core.workflow.orchestration import OnboardingOrchestrator
from database import get_database
from repositories import agent_executions as agent_executions_repo
from repositories import agents_repo
from repositories import approvals as approvals_repo
from repositories import tasks as tasks_repo
from repositories import workflows as workflows_repo
from services.scheduler import BackgroundScheduler

logger = get_logger(__name__)

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])


async def _stalled_workflows() -> List[Dict[str, Any]]:
    """Running workflows whose most recent task activity predates the escalation window."""
    running = await workflows_repo.list(status="running")
    stalled: List[Dict[str, Any]] = []
    now = datetime.utcnow()

    for row in running:
        last_activity_str = row.get("started_at") or row.get("updated_at")
        task_rows = await tasks_repo.list(workflow_id=row["id"], order_by="updated_at", descending=True, limit=1)
        if task_rows:
            last_activity_str = task_rows[0].get("updated_at") or last_activity_str
        if not last_activity_str:
            continue
        try:
            last_activity = datetime.fromisoformat(str(last_activity_str).replace("Z", ""))
        except ValueError:
            continue
        if (now - last_activity).total_seconds() > settings.escalation_timeout_seconds:
            stalled.append({**row, "last_activity_at": last_activity_str})

    return stalled


@router.get("/health")
async def monitoring_health() -> Dict[str, Any]:
    """Database reachability, registered agents/plugins, LLM provider, scheduler and feature flags."""
    db = get_database()
    reachable = await db.health()
    scheduler_running = bool(BackgroundScheduler._task and not BackgroundScheduler._task.done())

    return {
        "status": "ok" if reachable else "degraded",
        "environment": settings.environment,
        "database": {"adapter": db.name, "reachable": reachable},
        "agents": AgentRegistry.list_agents(),
        "plugins": {plugin["name"]: plugin["mode"] for plugin in PLUGIN_CATALOG},
        "llm_provider": LLMService.active_provider().name,
        "scheduler_running": scheduler_running,
        "feature_flags": {
            "enable_email": settings.enable_email,
            "enable_realtime": settings.enable_realtime,
            "enable_langgraph": settings.enable_langgraph,
            "enable_langfuse": settings.enable_langfuse,
            "enable_google_calendar": settings.enable_google_calendar,
            "enable_slack": settings.enable_slack,
            "enable_jira": settings.enable_jira,
            "enable_seed": settings.enable_seed,
        },
    }


@router.get("/metrics")
async def monitoring_metrics() -> Dict[str, Any]:
    """Aggregate operational metrics across workflows, tasks and agents."""
    workflow_rows = await workflows_repo.list()
    workflows_by_status: Dict[str, int] = {}
    for row in workflow_rows:
        status = row.get("status") or "unknown"
        workflows_by_status[status] = workflows_by_status.get(status, 0) + 1

    task_rows = await tasks_repo.list()
    completed_tasks = [t for t in task_rows if t.get("status") == "completed"]
    failed_tasks = [t for t in task_rows if t.get("status") == "failed"]
    finished_tasks = completed_tasks + failed_tasks
    success_rate = (len(completed_tasks) / len(finished_tasks)) if finished_tasks else None

    durations = []
    for task in completed_tasks:
        started, completed = task.get("started_at"), task.get("completed_at")
        if not started or not completed:
            continue
        try:
            delta = datetime.fromisoformat(str(completed).replace("Z", "")) - datetime.fromisoformat(
                str(started).replace("Z", "")
            )
            durations.append(delta.total_seconds())
        except ValueError:
            continue
    avg_task_duration_seconds = (sum(durations) / len(durations)) if durations else None

    agent_rows = await agents_repo.list()
    agent_stats = {
        row["name"]: {
            "total_executions": row.get("total_executions", 0),
            "successful_executions": row.get("successful_executions", 0),
            "failed_executions": row.get("failed_executions", 0),
            "avg_duration_seconds": row.get("avg_duration_seconds", 0.0),
        }
        for row in agent_rows
    }

    pending_approvals = await approvals_repo.list_pending()
    stalled = await _stalled_workflows()

    return {
        "workflows_by_status": workflows_by_status,
        "total_workflows": len(workflow_rows),
        "tasks": {
            "total": len(task_rows),
            "completed": len(completed_tasks),
            "failed": len(failed_tasks),
            "success_rate": success_rate,
            "avg_duration_seconds": avg_task_duration_seconds,
        },
        "agent_stats": agent_stats,
        "recent_agent_executions": len(await agent_executions_repo.list_recent(limit=100)),
        "pending_approvals": len(pending_approvals),
        "stalled_workflows": len(stalled),
    }


@router.post("/recover")
async def recover_stalled_workflows() -> Dict[str, Any]:
    """Re-enter the runtime for any running workflow that appears stalled."""
    stalled_before = await _stalled_workflows()
    await OnboardingOrchestrator.recover_stalled()
    return {"message": "Recovery sweep triggered.", "candidates": len(stalled_before)}


@router.get("/workflows/stalled")
async def stalled_workflows() -> List[Dict[str, Any]]:
    """Running workflows with no recent task activity."""
    return await _stalled_workflows()
