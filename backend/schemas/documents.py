"""Request/response models for documents."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class DocumentUploadRequest(BaseModel):
    """Metadata accompanying a multipart file upload."""

    document_type: str
    expiry_date: Optional[datetime] = None


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: Optional[str] = None
    employee_id: str
    document_type: str
    file_name: str
    file_type: str
    file_size: int = 0
    storage_path: Optional[str] = None
    storage_url: str
    status: str = "uploaded"
    required: bool = True
    validation_errors: List[str] = Field(default_factory=list)
    extracted_data: Dict[str, Any] = Field(default_factory=dict)
    expiry_date: Optional[datetime] = None
    verified_at: Optional[datetime] = None
    verified_by: Optional[str] = None
    uploaded_at: Optional[datetime] = None


class DocumentChecklistItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    document_type: str
    required: bool
    uploaded: bool
    status: str
    document_id: Optional[str] = None


class DocumentStatusUpdate(BaseModel):
    status: str
    verified_by: Optional[str] = None
    errors: Optional[List[str]] = None
