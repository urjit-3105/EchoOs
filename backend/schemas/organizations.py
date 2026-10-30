"""Request/response models for organizations."""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class OrganizationCreate(BaseModel):
    name: str
    slug: str
    industry: Optional[str] = None
    size: Optional[str] = None
    logo_url: Optional[str] = None
    timezone: str = "UTC"
    settings: Dict[str, Any] = Field(default_factory=dict)
    policies: Dict[str, Any] = Field(default_factory=dict)


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    industry: Optional[str] = None
    size: Optional[str] = None
    logo_url: Optional[str] = None
    timezone: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None
    policies: Optional[Dict[str, Any]] = None


class OrganizationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    slug: str
    industry: Optional[str] = None
    size: Optional[str] = None
    logo_url: Optional[str] = None
    timezone: str = "UTC"
    settings: Dict[str, Any] = Field(default_factory=dict)
    policies: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
