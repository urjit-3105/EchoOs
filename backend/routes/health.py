"""Liveness/readiness probe - mounted without the /api/v1 prefix so infra can hit /health directly."""

from typing import Any, Dict

from fastapi import APIRouter

from config.settings import settings
from database import get_database

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Basic liveness probe: app status, environment, persistence backend and version."""
    db = get_database()
    return {
        "status": "ok",
        "environment": settings.environment,
        "persistence": db.name,
        "version": "1.0.0",
    }
