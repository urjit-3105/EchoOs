"""Append-only audit trail writer.

Every mutating action in the platform (invitation sent, document uploaded,
approval resolved, ...) should call :meth:`AuditService.record`. Audit writes
must never be allowed to break the caller, so every failure is swallowed and
logged instead of raised.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from core.logger.structured import get_logger
from repositories import audit_logs

logger = get_logger(__name__)


class AuditService:
    """Thin, resilient wrapper around the ``audit_logs`` repository."""

    @staticmethod
    async def record(
        action: str,
        resource_type: str,
        resource_id: str,
        *,
        actor: Optional[str] = None,
        actor_type: str = "system",
        organization_id: Optional[str] = None,
        changes: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Write one audit row. Returns ``{}`` (never raises) when persistence fails."""
        payload = {
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "actor": actor,
            "actor_type": actor_type,
            "organization_id": organization_id,
            "changes": changes or {},
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
        }
        try:
            return await audit_logs.create(payload)
        except Exception as exc:  # pragma: no cover - audit is best-effort
            logger.error(
                "Failed to write audit log",
                context={"action": action, "resource_type": resource_type, "resource_id": resource_id},
                exc_info=exc,
            )
            return {}

    @staticmethod
    async def list_for(resource_type: str, resource_id: str) -> List[Dict[str, Any]]:
        try:
            return await audit_logs.list_for_resource(resource_type, resource_id)
        except Exception as exc:  # pragma: no cover
            logger.error("Failed to list audit logs for resource", exc_info=exc)
            return []

    @staticmethod
    async def recent(org_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        try:
            return await audit_logs.list_recent(org_id, limit)
        except Exception as exc:  # pragma: no cover
            logger.error("Failed to list recent audit logs", exc_info=exc)
            return []
