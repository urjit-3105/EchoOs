"""Repository for the ``execution_plans`` table."""

from typing import Any, Dict, Optional

from repositories.base import BaseRepository


class ExecutionPlanRepository(BaseRepository):
    table = "execution_plans"

    async def get_latest(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        rows = await self.list(workflow_id=workflow_id, order_by="created_at", descending=True, limit=1)
        return rows[0] if rows else None

    async def save_plan(self, workflow_id: str, plan_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Persist a freshly generated ``ExecutionPlanState``-shaped dict."""
        data = {
            "workflow_id": workflow_id,
            "plan_data": plan_dict,
            "critical_path": plan_dict.get("critical_path", []),
            "estimated_duration": plan_dict.get("estimated_total_duration", 0),
            "status": plan_dict.get("status", "generated"),
        }
        return await self.create(data)


execution_plans = ExecutionPlanRepository()
