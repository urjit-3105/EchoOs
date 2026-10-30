"""Document upload, checklist and local file serving."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from fastapi.responses import Response

from core.logger.structured import get_logger
from database.sql import SQLAlchemyAdapter
from repositories import documents as documents_repo
from repositories import employees as employees_repo
from schemas import DocumentStatusUpdate
from services.documents import DocumentService

logger = get_logger(__name__)

router = APIRouter(prefix="/documents", tags=["Documents"])

_CONTENT_TYPES = {
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "pdf": "application/pdf",
    "gif": "image/gif",
    "webp": "image/webp",
}


@router.get("/")
async def list_documents(employee_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """List documents, optionally scoped to one employee."""
    if employee_id:
        return await documents_repo.list_by_employee(employee_id)
    return await documents_repo.list(order_by="uploaded_at", descending=True)


@router.post("/upload")
async def upload_document(
    employee_id: str,
    document_type: str,
    file: UploadFile = File(...),
) -> Dict[str, Any]:
    """Upload a document file for an employee."""
    employee = await employees_repo.get(employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail=f"Employee '{employee_id}' not found.")

    content = await file.read()
    document = await DocumentService.upload(
        employee_id=employee_id,
        document_type=document_type,
        file_name=file.filename or document_type,
        content=content,
        content_type=file.content_type or "application/octet-stream",
        organization_id=employee.get("organization_id"),
    )
    return document


@router.get("/checklist/{employee_id}")
async def document_checklist(employee_id: str) -> List[Dict[str, Any]]:
    """Required vs. uploaded documents for an employee."""
    employee = await employees_repo.get(employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail=f"Employee '{employee_id}' not found.")
    return await DocumentService.checklist(employee_id)


@router.get("/types")
async def required_document_types(employee_id: str = Query(...)) -> Dict[str, Any]:
    """Required document types for an employee (based on department/role policy)."""
    employee = await employees_repo.get(employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail=f"Employee '{employee_id}' not found.")
    return {"employee_id": employee_id, "required_document_types": await DocumentService.required_for(employee)}


@router.patch("/{document_id}/status")
async def set_document_status(document_id: str, payload: DocumentStatusUpdate) -> Dict[str, Any]:
    """Transition a document's verification status."""
    existing = await documents_repo.get(document_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Document '{document_id}' not found.")
    updated = await DocumentService.set_status(
        document_id, payload.status, verified_by=payload.verified_by, errors=payload.errors
    )
    return updated or existing


@router.delete("/{document_id}")
async def delete_document(document_id: str) -> Dict[str, Any]:
    """Delete a document and its stored file."""
    existing = await documents_repo.get(document_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Document '{document_id}' not found.")
    deleted = await DocumentService.delete(document_id)
    return {"message": "Document deleted." if deleted else "Document could not be deleted.", "success": deleted}


@router.get("/files/{bucket}/{path:path}")
async def get_stored_file(bucket: str, path: str) -> Response:
    """Serve a locally stored document file back (used when Supabase Storage is not configured)."""
    content = SQLAlchemyAdapter.read_local_file(bucket, path)
    if content is None:
        raise HTTPException(status_code=404, detail="File not found.")
    extension = path.rsplit(".", 1)[-1].lower() if "." in path else ""
    media_type = _CONTENT_TYPES.get(extension, "application/octet-stream")
    return Response(content=content, media_type=media_type)
