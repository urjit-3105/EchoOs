"""Repository for the ``execution_logs`` table."""

from typing import Any, Dict, List

from repositories.base import BaseRepository


class ExecutionLogRepository(BaseRepository):
    table = "execution_logs"

    async def list_by_workflow(self, workflow_id: str, limit: int = 200) -> List[Dict[str, Any]]:
        return await self.list(workflow_id=workflow_id, order_by="timestamp", limit=limit)


execution_logs = ExecutionLogRepository()
