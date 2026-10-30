"""Request/response models for workflows and tasks."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class WorkflowActionRequest(BaseModel):
    """Pause / resume / cancel / retry - the action is interpreted by the route."""

    action: str
    reason: Optional[str] = None


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    workflow_id: str
    agent_id: Optional[str] = None
    agent_name: Optional[str] = None
    task_key: Optional[str] = None
    name: str
    description: Optional[str] = None
    tool_name: Optional[str] = None
    status: str = "pending"
    priority: int = 0
    dependencies: List[str] = Field(default_factory=list)
    input_data: Dict[str, Any] = Field(default_factory=dict)
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    retries: int = 0
    max_retries: int = 3
    requires_approval: bool = False
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class WorkflowResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: Optional[str] = None
    employee_id: str
    template_id: Optional[str] = None
    name: str
    status: str = "pending"
    current_stage: Optional[str] = None
    progress: int = 0
    state: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    tasks: List[TaskResponse] = Field(default_factory=list)


class OnboardingProgressResponse(BaseModel):
    """Portal-facing summary returned by ``services.onboarding.OnboardingService.progress``."""

    model_config = ConfigDict(from_attributes=True)

    invitation_accepted: bool
    profile_completed: bool
    documents: List[Dict[str, Any]] = Field(default_factory=list)
    terms_accepted: bool
    workflow: Optional[Dict[str, Any]] = None
    percent_complete: int = 0
    current_stage: Optional[str] = None
    status: Optional[str] = None
