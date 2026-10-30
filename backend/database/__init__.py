"""Database access point.

``db`` is the single object every repository imports. It resolves to the
Supabase adapter when the project is configured, and to the SQLAlchemy adapter
otherwise, so the application boots with or without cloud credentials.
"""

from typing import Optional

from config.settings import settings
from core.logger.structured import get_logger
from database.base import DatabaseAdapter
from database.sql import SQLAlchemyAdapter
from database.supabase import (
    SupabaseAdapter,
    get_supabase_anon_client,
    get_supabase_client,
)

logger = get_logger(__name__)

_adapter: Optional[DatabaseAdapter] = None


def get_database() -> DatabaseAdapter:
    """Resolve (and memoise) the active adapter."""
    global _adapter
    if _adapter is not None:
        return _adapter

    if settings.supabase_enabled and get_supabase_client() is not None:
        _adapter = SupabaseAdapter()
        logger.info("Persistence backend: Supabase")
    else:
        _adapter = SQLAlchemyAdapter()
        logger.info(
            "Persistence backend: SQLAlchemy",
            context={"reason": "Supabase credentials absent or invalid"},
        )
    return _adapter


def set_database(adapter: DatabaseAdapter) -> None:
    """Override the adapter - used by tests and the seed script."""
    global _adapter
    _adapter = adapter


async def init_database() -> DatabaseAdapter:
    """Called on application startup."""
    adapter = get_database()
    await adapter.connect()
    return adapter


class _DatabaseProxy:
    """Lazily forwards attribute access to the resolved adapter."""

    def __getattr__(self, item):
        return getattr(get_database(), item)

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<Database {get_database().name}>"


db = _DatabaseProxy()

__all__ = [
    "db",
    "get_database",
    "set_database",
    "init_database",
    "DatabaseAdapter",
    "SQLAlchemyAdapter",
    "SupabaseAdapter",
    "get_supabase_client",
    "get_supabase_anon_client",
]
