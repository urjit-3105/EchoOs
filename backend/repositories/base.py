"""Generic async repository sitting on top of the ``db`` adapter.

Every entity-specific repository subclasses :class:`BaseRepository` instead of
talking to ``database.db`` directly, so table-name typos and datetime
serialisation bugs only have to be fixed in one place. The Supabase adapter
requires JSON-safe payloads, so this layer is also the single spot where
datetimes get turned into ISO strings before hitting the wire.
"""

import uuid
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from database import db
from models.database import TABLE_MODELS


def _serialise(value: Any) -> Any:
    """Recursively turn datetimes into ISO strings so every adapter can store the payload."""
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _serialise(val) for key, val in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serialise(val) for val in value]
    return value


def _serialise_data(data: Dict[str, Any]) -> Dict[str, Any]:
    return {key: _serialise(value) for key, value in data.items()}


class BaseRepository:
    """Thin async CRUD wrapper around ``db`` scoped to a single table.

    Subclasses set ``table`` at class level and add entity-specific query
    helpers. Column presence is checked against ``models.database.TABLE_MODELS``
    so timestamp bookkeeping never fails on tables that don't have those
    columns (e.g. ``agent_executions`` has no ``updated_at``).
    """

    table: str = ""

    def __init__(self, table: Optional[str] = None):
        if table:
            self.table = table
        if not self.table:
            raise ValueError("A repository must be constructed with a table name.")

    # ------------------------------------------------------------------
    # Column introspection
    # ------------------------------------------------------------------
    def _columns(self) -> set:
        model = TABLE_MODELS.get(self.table)
        if model is None:
            return set()
        return set(model.__table__.c.keys())

    def _has_column(self, name: str) -> bool:
        return name in self._columns()

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a row, filling ``id`` and timestamps when the table has them."""
        payload = dict(data)
        payload.setdefault("id", str(uuid.uuid4()))

        now = datetime.utcnow().isoformat()
        if self._has_column("created_at") and not payload.get("created_at"):
            payload["created_at"] = now
        if self._has_column("updated_at") and not payload.get("updated_at"):
            payload["updated_at"] = now

        return await db.insert(self.table, _serialise_data(payload))

    async def get(self, record_id: str) -> Optional[Dict[str, Any]]:
        return await db.get(self.table, record_id)

    async def find_one(self, **filters) -> Optional[Dict[str, Any]]:
        return await db.find_one(self.table, filters)

    async def list(
        self,
        *,
        order_by: Optional[str] = None,
        descending: bool = False,
        limit: Optional[int] = None,
        offset: int = 0,
        **filters,
    ) -> List[Dict[str, Any]]:
        return await db.list(
            self.table,
            filters=filters or None,
            order_by=order_by,
            descending=descending,
            limit=limit,
            offset=offset,
        )

    async def update(self, record_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        payload = dict(data)
        if self._has_column("updated_at"):
            payload.setdefault("updated_at", datetime.utcnow().isoformat())
        return await db.update(self.table, record_id, _serialise_data(payload))

    async def delete(self, record_id: str) -> bool:
        return await db.delete(self.table, record_id)

    async def count(self, **filters) -> int:
        return await db.count(self.table, filters or None)

    async def upsert_by(self, field: str, value: Any, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update the row matching ``field == value``, or create it when absent."""
        existing = await self.find_one(**{field: value})
        payload = dict(data)
        payload[field] = value
        if existing:
            updated = await self.update(existing["id"], payload)
            return updated or existing
        return await self.create(payload)
