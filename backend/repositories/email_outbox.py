"""Repository for the ``email_outbox`` table."""

from typing import Any, Dict, List

from repositories.base import BaseRepository


class EmailOutboxRepository(BaseRepository):
    table = "email_outbox"

    async def list_recent(self, limit: int = 50) -> List[Dict[str, Any]]:
        return await self.list(order_by="created_at", descending=True, limit=limit)


email_outbox = EmailOutboxRepository()
