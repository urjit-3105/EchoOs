"""Repository for the ``users`` table (authenticated principals)."""

from typing import Any, Dict, Optional

from repositories.base import BaseRepository


class UserRepository(BaseRepository):
    table = "users"

    async def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        return await self.find_one(email=email.lower().strip())

    async def get_by_employee_id(self, employee_id: str) -> Optional[Dict[str, Any]]:
        return await self.find_one(employee_id=employee_id)


users = UserRepository()
