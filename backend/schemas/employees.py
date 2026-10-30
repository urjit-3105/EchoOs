"""Request/response models for employees."""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class EmployeeCreate(BaseModel):
    organization_id: str
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None
    department: Optional[str] = None
    role: Optional[str] = None
    job_title: Optional[str] = None
    employment_type: str = "full_time"
    manager_id: Optional[str] = None
    start_date: Optional[datetime] = None


class EmployeeUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    role: Optional[str] = None
    job_title: Optional[str] = None
    employment_type: Optional[str] = None
    manager_id: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[datetime] = None
    profile: Optional[Dict[str, Any]] = None


class ProfileCompletionRequest(BaseModel):
    """Submitted from the employee self-service portal."""

    profile: Dict[str, Any] = Field(default_factory=dict)
    phone: Optional[str] = None
    accept_terms: bool = False


class EmployeeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: Optional[str] = None
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None
    department: Optional[str] = None
    role: Optional[str] = None
    job_title: Optional[str] = None
    employment_type: str = "full_time"
    manager_id: Optional[str] = None
    status: str = "invited"
    onboarding_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    profile: Dict[str, Any] = Field(default_factory=dict)
    profile_completed: bool = False
    terms_accepted_at: Optional[datetime] = None
    policies_reviewed_at: Optional[datetime] = None
    activated_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
