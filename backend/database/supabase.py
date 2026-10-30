"""Supabase implementation of :class:`DatabaseAdapter`.

Wraps the synchronous ``supabase-py`` client in an executor so it satisfies the
same awaitable contract as the SQLAlchemy adapter. Also exposes Supabase Auth
and Supabase Storage helpers used by the auth service and the document service.
"""

import asyncio
from functools import lru_cache
from typing import Any, Dict, List, Optional

from config.settings import settings
from core.logger.structured import get_logger
from database.base import DatabaseAdapter

logger = get_logger(__name__)


@lru_cache(maxsize=1)
def get_supabase_client():
    """Service-role Supabase client. Returns ``None`` when Supabase is not configured."""
    if not settings.supabase_enabled:
        logger.warning("Supabase is not configured; falling back to the SQL adapter.")
        return None
    try:
        from supabase import create_client
    except ImportError:  # pragma: no cover - dependency missing
        logger.error("supabase package is not installed. Run: pip install supabase")
        return None

    try:
        client = create_client(settings.supabase_url, settings.supabase_secret_key)
        logger.info("Supabase client initialised", context={"url": settings.supabase_url})
        return client
    except Exception as exc:  # pragma: no cover - network/credential issues
        logger.error("Failed to initialise the Supabase client", exc_info=exc)
        return None


@lru_cache(maxsize=1)
def get_supabase_anon_client():
    """Anon-key client, used for password / magic-link auth flows."""
    if not settings.supabase_url.startswith("http"):
        return None
    key = settings.supabase_anon_key
    if not key or key.startswith("placeholder"):
        key = settings.supabase_secret_key
    if not key:
        return None
    try:
        from supabase import create_client

        return create_client(settings.supabase_url, key)
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to initialise the Supabase anon client", exc_info=exc)
        return None


class SupabaseAdapter(DatabaseAdapter):
    name = "supabase"

    def __init__(self):
        self._client = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    @property
    def client(self):
        if self._client is None:
            self._client = get_supabase_client()
        if self._client is None:
            raise RuntimeError("Supabase client unavailable. Check SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY.")
        return self._client

    async def connect(self) -> None:
        await self._run(lambda: self.client)
        logger.info("Supabase adapter ready", context={"url": settings.supabase_url})

    async def health(self) -> bool:
        def _check() -> bool:
            self.client.table("organizations").select("id").limit(1).execute()
            return True

        try:
            return await self._run(_check)
        except Exception as exc:
            logger.error("Supabase health check failed", exc_info=exc)
            return False

    async def _run(self, fn, *args):
        return await asyncio.get_event_loop().run_in_executor(None, fn, *args)

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    async def insert(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        rows = await self.insert_many(table, [data])
        return rows[0] if rows else data

    async def insert_many(self, table: str, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not rows:
            return []

        def _insert() -> List[Dict[str, Any]]:
            response = self.client.table(table).insert(rows).execute()
            return response.data or []

        return await self._run(_insert)

    async def get(self, table: str, record_id: str) -> Optional[Dict[str, Any]]:
        def _get() -> Optional[Dict[str, Any]]:
            response = self.client.table(table).select("*").eq("id", record_id).limit(1).execute()
            data = response.data or []
            return data[0] if data else None

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
        def _list() -> List[Dict[str, Any]]:
            query = self.client.table(table).select("*")
            for key, value in (filters or {}).items():
                if isinstance(value, (list, tuple, set)):
                    query = query.in_(key, list(value))
                elif value is None:
                    query = query.is_(key, "null")
                else:
                    query = query.eq(key, value)
            if order_by:
                query = query.order(order_by, desc=descending)
            if limit:
                query = query.range(offset, offset + limit - 1)
            elif offset:
                query = query.range(offset, offset + 999)
            return query.execute().data or []

        return await self._run(_list)

    async def update(self, table: str, record_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        payload = {k: v for k, v in data.items() if k != "id"}
        if not payload:
            return await self.get(table, record_id)

        def _update() -> Optional[Dict[str, Any]]:
            response = self.client.table(table).update(payload).eq("id", record_id).execute()
            rows = response.data or []
            return rows[0] if rows else None

        return await self._run(_update)

    async def delete(self, table: str, record_id: str) -> bool:
        def _delete() -> bool:
            response = self.client.table(table).delete().eq("id", record_id).execute()
            return bool(response.data)

        return await self._run(_delete)

    async def count(self, table: str, filters: Optional[Dict[str, Any]] = None) -> int:
        def _count() -> int:
            query = self.client.table(table).select("id", count="exact")
            for key, value in (filters or {}).items():
                if isinstance(value, (list, tuple, set)):
                    query = query.in_(key, list(value))
                else:
                    query = query.eq(key, value)
            response = query.execute()
            return response.count or 0

        return await self._run(_count)

    # ------------------------------------------------------------------
    # Storage
    # ------------------------------------------------------------------
    async def upload_file(
        self,
        bucket: str,
        path: str,
        content: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        def _upload() -> str:
            storage = self.client.storage
            try:
                storage.create_bucket(bucket, options={"public": True})
            except Exception:
                pass  # bucket already exists
            storage.from_(bucket).upload(
                path,
                content,
                {"content-type": content_type, "upsert": "true"},
            )
            return storage.from_(bucket).get_public_url(path)

        return await self._run(_upload)

    async def delete_file(self, bucket: str, path: str) -> bool:
        def _delete() -> bool:
            self.client.storage.from_(bucket).remove([path])
            return True

        try:
            return await self._run(_delete)
        except Exception as exc:
            logger.error("Supabase storage delete failed", exc_info=exc)
            return False
