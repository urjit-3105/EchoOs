"""Request/response models for ``services.auth.AuthService``."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    organization_id: Optional[str] = None
    role: str = "employee"
    employee_id: Optional[str] = None


class MagicLinkRequest(BaseModel):
    email: EmailStr


class MagicLinkVerifyRequest(BaseModel):
    token: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(min_length=8)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: EmailStr
    full_name: Optional[str] = None
    organization_id: Optional[str] = None
    role: str = "employee"
    employee_id: Optional[str] = None
    is_active: bool = True
    email_verified: bool = False
    last_login_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


class TokenResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user: UserResponse
    access_token: str
    token_type: str = "bearer"
