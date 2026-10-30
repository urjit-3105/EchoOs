"""Repository for the ``documents`` table."""

from typing import Any, Dict, List, Optional

from repositories.base import BaseRepository


class DocumentRepository(BaseRepository):
    table = "documents"

    async def list_by_employee(self, employee_id: str) -> List[Dict[str, Any]]:
        return await self.list(employee_id=employee_id, order_by="uploaded_at", descending=True)

    async def get_by_type(self, employee_id: str, document_type: str) -> Optional[Dict[str, Any]]:
        return await self.find_one(employee_id=employee_id, document_type=document_type)


documents = DocumentRepository()
