"""Repository for the ``employees`` table."""

from typing import Any, Dict, List, Optional

from repositories.base import BaseRepository


class EmployeeRepository(BaseRepository):
    table = "employees"

    async def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        return await self.find_one(email=email.lower().strip())

    async def list_by_organization(self, organization_id: str) -> List[Dict[str, Any]]:
        return await self.list(organization_id=organization_id, order_by="created_at", descending=True)

    async def count_by_status(self, organization_id: Optional[str] = None) -> Dict[str, int]:
        """Tally employees per status - powers the dashboard summary cards."""
        filters: Dict[str, Any] = {}
        if organization_id:
            filters["organization_id"] = organization_id
        rows = await self.list(**filters)
        counts: Dict[str, int] = {}
        for row in rows:
            status = row.get("status") or "unknown"
            counts[status] = counts.get(status, 0) + 1
        return counts

    async def set_status(self, employee_id: str, status: str) -> Optional[Dict[str, Any]]:
        return await self.update(employee_id, {"status": status})


employees = EmployeeRepository()
