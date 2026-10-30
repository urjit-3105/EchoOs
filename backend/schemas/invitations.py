"""Request/response models for invitations."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class InvitationCreate(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    organization_id: str
    role: str = "employee"
    department: Optional[str] = None
    job_title: Optional[str] = None
    invited_by: Optional[str] = None
    message: Optional[str] = None


class InvitationAcceptRequest(BaseModel):
    password: Optional[str] = None
    profile: Optional[dict] = None


class InvitationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: Optional[str] = None
    employee_id: Optional[str] = None
    email: EmailStr
    role: str = "employee"
    department: Optional[str] = None
    job_title: Optional[str] = None
    status: str = "pending"
    invited_by: Optional[str] = None
    message: Optional[str] = None
    expires_at: Optional[datetime] = None
    accepted_at: Optional[datetime] = None
    reminder_count: int = 0
    last_reminder_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


class InvitationCreateResponse(BaseModel):
    """What ``InvitationService.create`` returns - invitation + convenience links."""

    model_config = ConfigDict(from_attributes=True)

    invitation: InvitationResponse
    accept_url: str
    qr_code: str = Field(default="", description="data:image/png;base64,... or empty when qrcode is unavailable")
