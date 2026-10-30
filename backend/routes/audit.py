"""Read-only access to the append-only audit trail."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query

from core.logger.structured import get_logger
from repositories import audit_logs
from services.audit import AuditService

logger = get_logger(__name__)

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get("/")
async def list_audit_logs(
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    organization_id: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
) -> List[Dict[str, Any]]:
    """List audit log entries with optional filters."""
    filters: Dict[str, Any] = {}
    if resource_type:
        filters["resource_type"] = resource_type
    if resource_id:
        filters["resource_id"] = resource_id
    if organization_id:
        filters["organization_id"] = organization_id
    if action:
        filters["action"] = action
    return await audit_logs.list(order_by="timestamp", descending=True, limit=limit, **filters)


@router.get("/resource/{resource_type}/{resource_id}")
async def get_resource_audit_log(resource_type: str, resource_id: str) -> List[Dict[str, Any]]:
    """Full audit history for one resource."""
    return await AuditService.list_for(resource_type, resource_id)
