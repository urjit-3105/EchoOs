"""Shared response envelopes used across every route module."""

from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class MessageResponse(BaseModel):
    """Generic ack payload for actions that don't return a resource."""

    model_config = ConfigDict(from_attributes=True)

    message: str
    success: bool = True


class PaginatedResponse(BaseModel, Generic[T]):
    """Envelope for any list endpoint that supports paging."""

    model_config = ConfigDict(from_attributes=True)

    items: List[T] = Field(default_factory=list)
    total: int = 0
    limit: Optional[int] = None
    offset: int = 0


class DashboardStats(BaseModel):
    """Top-level counters shown on the admin/HR dashboard."""

    model_config = ConfigDict(from_attributes=True)

    total_employees: int = 0
    employees_by_status: Dict[str, int] = Field(default_factory=dict)
    active_workflows: int = 0
    pending_approvals: int = 0
    pending_invitations: int = 0
    unread_notifications: int = 0
    documents_pending_review: int = 0
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    detail: str
    code: Optional[str] = None
    extra: Optional[Dict[str, Any]] = None
