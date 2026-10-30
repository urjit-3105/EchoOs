"""In-app notification service.

Writes a ``notifications`` row for every noteworthy event and republishes it on
the :class:`EventBus` so a websocket/SSE layer can push it live. Never raises:
a notification failure must not abort the workflow step that triggered it.
"""

from typing import Any, Dict, List, Optional

from core.events.bus import EventBus
from core.logger.structured import get_logger
from repositories import notifications

logger = get_logger(__name__)


class NotificationService:
    """Resilient wrapper around the ``notifications`` repository + event bus."""

    @staticmethod
    async def push(
        *,
        type: str,
        title: str,
        message: str,
        category: str = "workflow",
        organization_id: Optional[str] = None,
        employee_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        user_id: Optional[str] = None,
        action_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        payload = {
            "type": type,
            "category": category,
            "title": title,
            "message": message,
            "organization_id": organization_id,
            "employee_id": employee_id,
            "workflow_id": workflow_id,
            "user_id": user_id,
            "action_url": action_url,
            "metadata_json": metadata or {},
        }
        try:
            row = await notifications.create(payload)
        except Exception as exc:  # pragma: no cover - notifications are best-effort
            logger.error("Failed to persist notification", context={"title": title}, exc_info=exc)
            return {}

        try:
            await EventBus.publish("Notification.Created", row)
        except Exception as exc:  # pragma: no cover
            logger.error("Failed to publish Notification.Created", exc_info=exc)

        return row

    @staticmethod
    async def recent(organization_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        try:
            return await notifications.list_recent(organization_id, limit)
        except Exception as exc:  # pragma: no cover
            logger.error("Failed to list notifications", exc_info=exc)
            return []

    @staticmethod
    async def mark_read(notification_id: str) -> Optional[Dict[str, Any]]:
        try:
            return await notifications.mark_read(notification_id)
        except Exception as exc:  # pragma: no cover
            logger.error("Failed to mark notification read", exc_info=exc)
            return None

    @staticmethod
    async def mark_all_read(organization_id: Optional[str] = None) -> int:
        try:
            return await notifications.mark_all_read(organization_id)
        except Exception as exc:  # pragma: no cover
            logger.error("Failed to mark all notifications read", exc_info=exc)
            return 0

    @staticmethod
    async def unread_count(organization_id: Optional[str] = None) -> int:
        try:
            return await notifications.unread_count(organization_id)
        except Exception as exc:  # pragma: no cover
            logger.error("Failed to count unread notifications", exc_info=exc)
            return 0
