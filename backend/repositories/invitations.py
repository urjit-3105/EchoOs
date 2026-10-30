"""Repository for the ``invitations`` table."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from repositories.base import BaseRepository


class InvitationRepository(BaseRepository):
    table = "invitations"

    async def get_by_token(self, token: str) -> Optional[Dict[str, Any]]:
        return await self.find_one(token=token)

    async def list_pending(self, organization_id: Optional[str] = None) -> List[Dict[str, Any]]:
        filters: Dict[str, Any] = {"status": "pending"}
        if organization_id:
            filters["organization_id"] = organization_id
        return await self.list(**filters)

    async def mark_accepted(self, invitation_id: str) -> Optional[Dict[str, Any]]:
        return await self.update(
            invitation_id,
            {"status": "accepted", "accepted_at": datetime.utcnow().isoformat()},
        )

    async def mark_expired(self, invitation_id: str) -> Optional[Dict[str, Any]]:
        return await self.update(invitation_id, {"status": "expired"})


invitations = InvitationRepository()
