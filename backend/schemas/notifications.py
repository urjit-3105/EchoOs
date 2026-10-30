"""Request/response models for notifications."""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class NotificationCreate(BaseModel):
    type: str
    title: str
    message: str
    category: str = "workflow"
    organization_id: Optional[str] = None
    employee_id: Optional[str] = None
    workflow_id: Optional[str] = None
    user_id: Optional[str] = None
    action_url: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: Optional[str] = None
    user_id: Optional[str] = None
    employee_id: Optional[str] = None
    workflow_id: Optional[str] = None
    type: str
    category: str = "workflow"
    title: str
    message: str
    action_url: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    is_read: bool = False
    created_at: Optional[datetime] = None
