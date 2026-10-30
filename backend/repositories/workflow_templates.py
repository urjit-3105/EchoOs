"""Repository for the ``workflow_templates`` table."""

from typing import Any, Dict, Optional

from repositories.base import BaseRepository


class WorkflowTemplateRepository(BaseRepository):
    table = "workflow_templates"

    async def get_by_key(self, key: str) -> Optional[Dict[str, Any]]:
        return await self.find_one(key=key)

    async def upsert_definition(
        self,
        key: str,
        name: str,
        description: Optional[str],
        definition: Dict[str, Any],
    ) -> Dict[str, Any]:
        existing = await self.get_by_key(key)
        payload = {
            "key": key,
            "name": name,
            "description": description,
            "definition": definition,
        }
        if existing:
            updated = await self.update(existing["id"], payload)
            return updated or existing
        return await self.create(payload)


workflow_templates = WorkflowTemplateRepository()
