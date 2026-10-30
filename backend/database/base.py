"""Storage abstraction shared by every repository.

Two adapters implement this interface:

* ``SQLAlchemyAdapter``  - local Postgres / SQLite, always available.
* ``SupabaseAdapter``    - the hosted Supabase Postgres via PostgREST.

Repositories only ever talk to this interface, so switching between the two is a
configuration concern rather than a code change.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class DatabaseAdapter(ABC):
    """Table oriented CRUD contract, modelled on the Supabase client surface."""

    name: str = "base"

    @abstractmethod
    async def connect(self) -> None:
        """Prepare the underlying connection / create tables when relevant."""

    @abstractmethod
    async def health(self) -> bool:
        """Return True when the datastore answers."""

    @abstractmethod
    async def insert(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a single row and return the stored representation."""

    @abstractmethod
    async def insert_many(self, table: str, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Insert several rows in one round trip."""

    @abstractmethod
    async def get(self, table: str, record_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a row by primary key."""

    @abstractmethod
    async def find_one(self, table: str, filters: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Fetch the first row matching an equality filter set."""

    @abstractmethod
    async def list(
        self,
        table: str,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        descending: bool = False,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List rows matching an equality filter set.

        ``filters`` values may be a scalar (equality) or a list (IN clause).
        """

    @abstractmethod
    async def update(self, table: str, record_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Patch a row by primary key and return the new representation."""

    @abstractmethod
    async def delete(self, table: str, record_id: str) -> bool:
        """Remove a row by primary key."""

    @abstractmethod
    async def count(self, table: str, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count rows matching an equality filter set."""

    # -- Object storage -------------------------------------------------
    @abstractmethod
    async def upload_file(
        self,
        bucket: str,
        path: str,
        content: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Persist a binary object and return a retrievable URL."""

    @abstractmethod
    async def delete_file(self, bucket: str, path: str) -> bool:
        """Remove a stored object."""
