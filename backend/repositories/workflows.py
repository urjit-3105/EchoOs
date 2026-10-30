"""Repository for the ``workflows`` table."""

from typing import Any, Dict, List, Optional

from repositories.base import BaseRepository

ACTIVE_STATUSES = ["pending", "running", "paused"]


class WorkflowRepository(BaseRepository):
    table = "workflows"

    async def list_by_employee(self, employee_id: str) -> List[Dict[str, Any]]:
        return await self.list(employee_id=employee_id, order_by="created_at", descending=True)

    async def get_active_for_employee(self, employee_id: str) -> Optional[Dict[str, Any]]:
        """Used to guard against starting a second workflow for the same employee."""
        rows = await self.list(employee_id=employee_id)
        for row in rows:
            if row.get("status") in ACTIVE_STATUSES:
                return row
        return None

    async def list_active(self) -> List[Dict[str, Any]]:
        rows = await self.list()
        return [row for row in rows if row.get("status") in ACTIVE_STATUSES]


workflows = WorkflowRepository()
