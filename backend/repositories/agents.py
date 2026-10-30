"""Repository for the ``agents`` table (the registry's persisted counterpart)."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from repositories.base import BaseRepository


class AgentRepository(BaseRepository):
    table = "agents"

    async def get_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        return await self.find_one(name=name)

    async def ensure_registered(
        self,
        name: str,
        description: Optional[str] = None,
        capabilities: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Create the agent row on first sight, otherwise leave counters untouched."""
        existing = await self.get_by_name(name)
        if existing:
            return existing
        return await self.create(
            {
                "name": name,
                "role_description": description,
                "capabilities": capabilities or [],
            }
        )

    async def record_execution(self, name: str, success: bool, duration: float) -> Optional[Dict[str, Any]]:
        """Roll a completed execution into the running average / success counters."""
        agent = await self.ensure_registered(name)
        total = int(agent.get("total_executions") or 0) + 1
        successful = int(agent.get("successful_executions") or 0) + (1 if success else 0)
        failed = int(agent.get("failed_executions") or 0) + (0 if success else 1)
        prior_avg = float(agent.get("avg_duration_seconds") or 0.0)
        prior_total = int(agent.get("total_executions") or 0)
        new_avg = ((prior_avg * prior_total) + duration) / total if total else duration

        return await self.update(
            agent["id"],
            {
                "total_executions": total,
                "successful_executions": successful,
                "failed_executions": failed,
                "avg_duration_seconds": new_avg,
                "last_active_at": datetime.utcnow().isoformat(),
            },
        )


agents_repo = AgentRepository()
