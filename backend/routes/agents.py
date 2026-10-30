"""Agent catalogue, tool/plugin catalogue, execution history and LLM status."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from core.agents import AGENT_CATALOG
from core.execution.plugins import PLUGIN_CATALOG
from core.llm.service import LLMService
from core.logger.structured import get_logger
from repositories import agent_executions as agent_executions_repo
from repositories import agents_repo

logger = get_logger(__name__)

router = APIRouter(prefix="/agents", tags=["Agents"])


async def _agent_view(entry: Dict[str, Any]) -> Dict[str, Any]:
    row = await agents_repo.get_by_name(entry["name"])
    return {
        **entry,
        "is_active": bool(row.get("is_active")) if row else True,
        "total_executions": (row or {}).get("total_executions", 0),
        "successful_executions": (row or {}).get("successful_executions", 0),
        "failed_executions": (row or {}).get("failed_executions", 0),
        "avg_duration_seconds": (row or {}).get("avg_duration_seconds", 0.0),
        "last_active_at": (row or {}).get("last_active_at"),
    }


@router.get("/")
async def list_agents() -> List[Dict[str, Any]]:
    """Merge static agent capability metadata with live execution counters."""
    return [await _agent_view(entry) for entry in AGENT_CATALOG]


@router.get("/tools")
async def list_tools() -> List[Dict[str, Any]]:
    """The plugin/tool catalogue with live configured status and mode (live/simulated)."""
    return PLUGIN_CATALOG


@router.get("/executions")
async def list_agent_executions(
    workflow_id: Optional[str] = None,
    agent_name: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
) -> List[Dict[str, Any]]:
    """List agent execution records, optionally filtered by workflow/agent."""
    filters: Dict[str, Any] = {}
    if workflow_id:
        filters["workflow_id"] = workflow_id
    if agent_name:
        filters["agent_name"] = agent_name
    return await agent_executions_repo.list(order_by="started_at", descending=True, limit=limit, **filters)


@router.get("/llm")
async def llm_status() -> Dict[str, Any]:
    """The active LLM provider and which providers are configured. Never leaks key values."""
    from config.settings import settings

    active = LLMService.active_provider()
    return {
        "active_provider": active.name,
        "configured_provider_setting": settings.llm_provider,
        "providers": {
            "gemini": settings.gemini_enabled,
            "groq": settings.groq_enabled,
            "openai": settings.openai_enabled,
            "rules": True,
        },
    }


@router.get("/{name}")
async def get_agent(name: str) -> Dict[str, Any]:
    """Fetch one agent's capability metadata + live counters. Declared after static paths."""
    entry = next((item for item in AGENT_CATALOG if item["name"] == name), None)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Agent '{name}' not found.")
    return await _agent_view(entry)


@router.get("/{name}/executions")
async def get_agent_executions(name: str, limit: int = Query(100, ge=1, le=1000)) -> List[Dict[str, Any]]:
    """Execution history for one agent."""
    return await agent_executions_repo.list(agent_name=name, order_by="started_at", descending=True, limit=limit)
