"""Repository for the ``approvals`` table (human-in-the-loop gates)."""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from repositories.base import BaseRepository


class ApprovalRepository(BaseRepository):
    table = "approvals"

    async def list_pending(self, organization_id: Optional[str] = None) -> List[Dict[str, Any]]:
        filters: Dict[str, Any] = {"status": "pending"}
        if organization_id:
            filters["organization_id"] = organization_id
        return await self.list(**filters, order_by="created_at")

    async def get_for_task(self, workflow_id: str, task_id: str) -> Optional[Dict[str, Any]]:
        return await self.find_one(workflow_id=workflow_id, task_id=task_id)

    async def list_stale(self, older_than_seconds: int) -> List[Dict[str, Any]]:
        """Pending approvals whose request is older than the given age - feeds reminders/escalation."""
        cutoff = datetime.utcnow() - timedelta(seconds=older_than_seconds)
        pending = await self.list(status="pending")
        stale = []
        for row in pending:
            created_at = row.get("created_at")
            if not created_at:
                continue
            try:
                created = datetime.fromisoformat(str(created_at).replace("Z", ""))
            except ValueError:
                continue
            if created <= cutoff:
                stale.append(row)
        return stale


approvals = ApprovalRepository()
