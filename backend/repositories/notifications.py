"""Repository for the ``notifications`` table."""

from typing import Any, Dict, List, Optional

from repositories.base import BaseRepository


class NotificationRepository(BaseRepository):
    table = "notifications"

    async def list_recent(self, organization_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        filters: Dict[str, Any] = {}
        if organization_id:
            filters["organization_id"] = organization_id
        return await self.list(**filters, order_by="created_at", descending=True, limit=limit)

    async def mark_read(self, notification_id: str) -> Optional[Dict[str, Any]]:
        return await self.update(notification_id, {"is_read": True})

    async def mark_all_read(self, organization_id: Optional[str] = None) -> int:
        filters: Dict[str, Any] = {"is_read": False}
        if organization_id:
            filters["organization_id"] = organization_id
        rows = await self.list(**filters)
        for row in rows:
            await self.update(row["id"], {"is_read": True})
        return len(rows)

    async def unread_count(self, organization_id: Optional[str] = None) -> int:
        filters: Dict[str, Any] = {"is_read": False}
        if organization_id:
            filters["organization_id"] = organization_id
        return await self.count(**filters)


notifications = NotificationRepository()
