"""Repository for the ``tasks`` table (per-workflow task instances)."""

from typing import Any, Dict, List, Optional

from repositories.base import BaseRepository


class TaskRepository(BaseRepository):
    table = "tasks"

    async def list_by_workflow(self, workflow_id: str) -> List[Dict[str, Any]]:
        return await self.list(workflow_id=workflow_id, order_by="created_at")

    async def get_by_key(self, workflow_id: str, task_key: str) -> Optional[Dict[str, Any]]:
        return await self.find_one(workflow_id=workflow_id, task_key=task_key)

    async def upsert_from_plan(self, workflow_id: str, task_plan_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Materialise a ``TaskPlanState``-shaped dict from the planner as a DB row.

        Accepts either the pydantic-model-dump field names (``task_id``,
        ``assigned_agent``, ``retry_policy``) or the raw workflow YAML shape, so
        the planner and the workflow loader can both feed this without translation.
        """
        task_key = task_plan_dict.get("task_id") or task_plan_dict.get("id") or task_plan_dict.get("task_key")
        retry_policy = task_plan_dict.get("retry_policy") or {}
        max_retries = retry_policy.get("max_retries") if isinstance(retry_policy, dict) else None

        data = {
            "workflow_id": workflow_id,
            "task_key": task_key,
            "name": task_plan_dict.get("name", task_key),
            "description": task_plan_dict.get("description"),
            "agent_name": task_plan_dict.get("assigned_agent") or task_plan_dict.get("agent_name") or task_plan_dict.get("agent"),
            "tool_name": task_plan_dict.get("tool_name") or task_plan_dict.get("tool"),
            "priority": task_plan_dict.get("priority", 0),
            "dependencies": task_plan_dict.get("dependencies") or task_plan_dict.get("depends_on") or [],
            "status": task_plan_dict.get("status", "pending"),
            "max_retries": max_retries if max_retries is not None else 3,
            "requires_approval": bool(task_plan_dict.get("requires_approval", False)),
        }

        existing = await self.get_by_key(workflow_id, task_key)
        if existing:
            updated = await self.update(existing["id"], data)
            return updated or existing
        return await self.create(data)


tasks = TaskRepository()
