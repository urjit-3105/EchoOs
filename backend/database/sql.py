"""SQLAlchemy implementation of :class:`DatabaseAdapter`.

Backs local development (SQLite by default) and any self-hosted Postgres,
including the direct ``DATABASE_URL`` connection string a Supabase project
exposes. All blocking driver calls are pushed onto the default executor so the
adapter stays awaitable alongside the Supabase one.
"""

import asyncio
import base64
import os
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import create_engine, delete as sa_delete, func, insert as sa_insert, select, update as sa_update
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool

from config.settings import settings
from core.logger.structured import get_logger
from database.base import DatabaseAdapter
from models.database import Base, TABLE_MODELS

logger = get_logger(__name__)

# Local object storage root used when Supabase Storage is unavailable.
LOCAL_STORAGE_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "storage")


def _serialise(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _serialise(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_serialise(v) for v in value]
    return value


def _row_to_dict(row: Any) -> Dict[str, Any]:
    return {key: _serialise(value) for key, value in dict(row._mapping).items()}


def _coerce_for_column(column: Any, value: Any) -> Any:
    """Turn ISO strings back into datetimes for DateTime columns."""
    if value is None:
        return None
    python_type = getattr(column.type, "python_type", None)
    try:
        if python_type is datetime and isinstance(value, str):
            return datetime.fromisoformat(value.replace("Z", "+00:00").replace("+00:00", ""))
    except (NotImplementedError, ValueError):
        return value
    return value


class SQLAlchemyAdapter(DatabaseAdapter):
    name = "sqlalchemy"

    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or settings.database_url
        self._engine: Optional[Engine] = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    @property
    def engine(self) -> Engine:
        if self._engine is None:
            kwargs: Dict[str, Any] = {"future": True, "pool_pre_ping": True}
            if self.database_url.startswith("sqlite"):
                kwargs["connect_args"] = {"check_same_thread": False}
                if ":memory:" in self.database_url:
                    kwargs["poolclass"] = StaticPool
                kwargs.pop("pool_pre_ping", None)
            self._engine = create_engine(self.database_url, **kwargs)
        return self._engine

    async def connect(self) -> None:
        await asyncio.get_event_loop().run_in_executor(None, self._create_all)
        logger.info("SQL adapter ready", context={"url": self._safe_url()})

    def _create_all(self) -> None:
        Base.metadata.create_all(self.engine)
        os.makedirs(LOCAL_STORAGE_ROOT, exist_ok=True)

    def _safe_url(self) -> str:
        if "@" in self.database_url:
            scheme, _, rest = self.database_url.partition("://")
            return f"{scheme}://***@{rest.split('@')[-1]}"
        return self.database_url

    async def health(self) -> bool:
        def _check() -> bool:
            with self.engine.connect() as conn:
                conn.exec_driver_sql("SELECT 1")
            return True

        try:
            return await asyncio.get_event_loop().run_in_executor(None, _check)
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("SQL health check failed", exc_info=exc)
            return False

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _table(self, table: str):
        model = TABLE_MODELS.get(table)
        if model is None:
            raise ValueError(f"Unknown table '{table}'.")
        return model.__table__

    def _apply_filters(self, stmt, table_obj, filters: Optional[Dict[str, Any]]):
        for key, value in (filters or {}).items():
            column = table_obj.c.get(key)
            if column is None:
                continue
            if isinstance(value, (list, tuple, set)):
                stmt = stmt.where(column.in_(list(value)))
            elif value is None:
                stmt = stmt.where(column.is_(None))
            else:
                stmt = stmt.where(column == _coerce_for_column(column, value))
        return stmt

    def _prepare_values(self, table_obj, data: Dict[str, Any]) -> Dict[str, Any]:
        values: Dict[str, Any] = {}
        for key, value in data.items():
            column = table_obj.c.get(key)
            if column is None:
                continue
            values[key] = _coerce_for_column(column, value)
        return values

    async def _run(self, fn, *args):
        return await asyncio.get_event_loop().run_in_executor(None, fn, *args)

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    async def insert(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        rows = await self.insert_many(table, [data])
        return rows[0]

    async def insert_many(self, table: str, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not rows:
            return []
        table_obj = self._table(table)

        def _insert() -> List[Dict[str, Any]]:
            prepared = [self._prepare_values(table_obj, row) for row in rows]
            with self.engine.begin() as conn:
                conn.execute(sa_insert(table_obj), prepared)
                ids = [row.get("id") for row in prepared if row.get("id")]
                if not ids:
                    return prepared
                result = conn.execute(select(table_obj).where(table_obj.c.id.in_(ids)))
                return [_row_to_dict(r) for r in result]

        return await self._run(_insert)

    async def get(self, table: str, record_id: str) -> Optional[Dict[str, Any]]:
        table_obj = self._table(table)

        def _get() -> Optional[Dict[str, Any]]:
            with self.engine.connect() as conn:
                row = conn.execute(select(table_obj).where(table_obj.c.id == record_id)).first()
                return _row_to_dict(row) if row else None

        return await self._run(_get)

    async def find_one(self, table: str, filters: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        results = await self.list(table, filters=filters, limit=1)
        return results[0] if results else None

    async def list(
        self,
        table: str,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        descending: bool = False,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        table_obj = self._table(table)

        def _list() -> List[Dict[str, Any]]:
            stmt = self._apply_filters(select(table_obj), table_obj, filters)
            if order_by and order_by in table_obj.c:
                column = table_obj.c[order_by]
                stmt = stmt.order_by(column.desc() if descending else column.asc())
            if limit:
                stmt = stmt.limit(limit)
            if offset:
                stmt = stmt.offset(offset)
            with self.engine.connect() as conn:
                return [_row_to_dict(row) for row in conn.execute(stmt)]

        return await self._run(_list)

    async def update(self, table: str, record_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        table_obj = self._table(table)

        def _update() -> Optional[Dict[str, Any]]:
            values = self._prepare_values(table_obj, data)
            values.pop("id", None)
            if not values:
                return None
            with self.engine.begin() as conn:
                conn.execute(sa_update(table_obj).where(table_obj.c.id == record_id).values(**values))
                row = conn.execute(select(table_obj).where(table_obj.c.id == record_id)).first()
                return _row_to_dict(row) if row else None

        return await self._run(_update)

    async def delete(self, table: str, record_id: str) -> bool:
        table_obj = self._table(table)

        def _delete() -> bool:
            with self.engine.begin() as conn:
                result = conn.execute(sa_delete(table_obj).where(table_obj.c.id == record_id))
                return bool(result.rowcount)

        return await self._run(_delete)

    async def count(self, table: str, filters: Optional[Dict[str, Any]] = None) -> int:
        table_obj = self._table(table)

        def _count() -> int:
            stmt = self._apply_filters(select(func.count()).select_from(table_obj), table_obj, filters)
            with self.engine.connect() as conn:
                return int(conn.execute(stmt).scalar() or 0)

        return await self._run(_count)

    # ------------------------------------------------------------------
    # Storage (local filesystem fallback)
    # ------------------------------------------------------------------
    async def upload_file(
        self,
        bucket: str,
        path: str,
        content: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        def _write() -> str:
            target_dir = os.path.join(LOCAL_STORAGE_ROOT, bucket, os.path.dirname(path))
            os.makedirs(target_dir, exist_ok=True)
            full_path = os.path.join(LOCAL_STORAGE_ROOT, bucket, path)
            with open(full_path, "wb") as handle:
                handle.write(content)
            return f"{settings.backend_url}{settings.api_v1_str}/documents/files/{bucket}/{path}"

        return await self._run(_write)

    async def delete_file(self, bucket: str, path: str) -> bool:
        def _remove() -> bool:
            full_path = os.path.join(LOCAL_STORAGE_ROOT, bucket, path)
            if os.path.exists(full_path):
                os.remove(full_path)
                return True
            return False

        return await self._run(_remove)

    @staticmethod
    def read_local_file(bucket: str, path: str) -> Optional[bytes]:
        full_path = os.path.join(LOCAL_STORAGE_ROOT, bucket, path)
        if not os.path.exists(full_path):
            return None
        with open(full_path, "rb") as handle:
            return handle.read()

    @staticmethod
    def encode_inline(content: bytes, content_type: str) -> str:
        return f"data:{content_type};base64,{base64.b64encode(content).decode()}"
