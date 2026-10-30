"""Repository for the ``verification_reports`` table."""

from typing import Any, Dict, Optional

from repositories.base import BaseRepository


class VerificationReportRepository(BaseRepository):
    table = "verification_reports"

    async def get_latest(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        rows = await self.list(workflow_id=workflow_id, order_by="created_at", descending=True, limit=1)
        return rows[0] if rows else None


verification_reports = VerificationReportRepository()
