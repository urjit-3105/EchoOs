"""Repository for the ``agent_executions`` table (per-invocation audit trail)."""

from typing import Any, Dict, List

from repositories.base import BaseRepository


class AgentExecutionRepository(BaseRepository):
    table = "agent_executions"

    async def list_by_workflow(self, workflow_id: str) -> List[Dict[str, Any]]:
        return await self.list(workflow_id=workflow_id, order_by="started_at")

    async def list_recent(self, limit: int = 50) -> List[Dict[str, Any]]:
        return await self.list(order_by="started_at", descending=True, limit=limit)


agent_executions = AgentExecutionRepository()
