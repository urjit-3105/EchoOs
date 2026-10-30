"""Repository for the ``audit_logs`` table."""

from typing import Any, Dict, List, Optional

from repositories.base import BaseRepository


class AuditLogRepository(BaseRepository):
    table = "audit_logs"

    async def list_for_resource(self, resource_type: str, resource_id: str) -> List[Dict[str, Any]]:
        return await self.list(
            resource_type=resource_type,
            resource_id=resource_id,
            order_by="timestamp",
            descending=True,
        )

    async def list_recent(self, organization_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        filters: Dict[str, Any] = {}
        if organization_id:
            filters["organization_id"] = organization_id
        return await self.list(**filters, order_by="timestamp", descending=True, limit=limit)


audit_logs = AuditLogRepository()
