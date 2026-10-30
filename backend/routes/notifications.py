"""In-app notifications."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from core.logger.structured import get_logger
from repositories import notifications as notifications_repo
from services.notifications import NotificationService

logger = get_logger(__name__)

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/")
async def list_notifications(
    organization_id: Optional[str] = None,
    unread_only: bool = False,
    limit: int = Query(50, ge=1, le=500),
) -> List[Dict[str, Any]]:
    """List recent notifications, optionally scoped to unread-only."""
    rows = await NotificationService.recent(organization_id, limit)
    if unread_only:
        rows = [row for row in rows if not row.get("is_read")]
    return rows


@router.get("/unread-count")
async def unread_count(organization_id: Optional[str] = None) -> Dict[str, int]:
    """Count of unread notifications."""
    return {"unread_count": await NotificationService.unread_count(organization_id)}


@router.post("/{notification_id}/read")
async def mark_read(notification_id: str) -> Dict[str, Any]:
    """Mark one notification as read."""
    updated = await NotificationService.mark_read(notification_id)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Notification '{notification_id}' not found.")
    return updated


@router.post("/read-all")
async def mark_all_read(organization_id: Optional[str] = None) -> Dict[str, Any]:
    """Mark every notification (optionally scoped to an org) as read."""
    count = await NotificationService.mark_all_read(organization_id)
    return {"message": f"Marked {count} notifications as read.", "count": count}


@router.delete("/{notification_id}")
async def delete_notification(notification_id: str) -> Dict[str, Any]:
    """Delete a notification."""
    existing = await notifications_repo.get(notification_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Notification '{notification_id}' not found.")
    deleted = await notifications_repo.delete(notification_id)
    return {"message": "Notification deleted." if deleted else "Could not delete notification.", "success": deleted}
