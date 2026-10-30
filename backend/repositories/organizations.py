"""Repository for the ``organizations`` table (tenancy root)."""

from typing import Any, Dict, Optional

from repositories.base import BaseRepository


class OrganizationRepository(BaseRepository):
    table = "organizations"

    async def get_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        return await self.find_one(slug=slug)

    async def get_default(self) -> Optional[Dict[str, Any]]:
        """First organization created - used as the tenant when none is specified."""
        rows = await self.list(order_by="created_at", limit=1)
        return rows[0] if rows else None


organizations = OrganizationRepository()
