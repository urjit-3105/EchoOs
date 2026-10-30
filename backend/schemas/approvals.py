"""Request/response models for approvals."""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class ApprovalRequestCreate(BaseModel):
    workflow_id: str
    task_id: str
    title: str
    description: str
    reason: str
    employee_id: Optional[str] = None
    organization_id: Optional[str] = None
    required_role: str = "hr"
    payload: Dict[str, Any] = Field(default_factory=dict)


class ApprovalDecision(BaseModel):
    approved: bool
    approver_email: Optional[str] = None
    approver_id: Optional[str] = None
    comments: Optional[str] = None


class ApprovalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: Optional[str] = None
    workflow_id: str
    task_id: Optional[str] = None
    employee_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    reason: Optional[str] = None
    status: str = "pending"
    requested_by: Optional[str] = None
    required_role: str = "hr"
    approver_id: Optional[str] = None
    approver_email: Optional[str] = None
    comments: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    reminder_count: int = 0
    last_reminder_at: Optional[datetime] = None
    escalated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
