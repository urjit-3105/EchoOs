"""Document upload, checklist and verification-status bookkeeping.

Requirements come from ``config/rules.yaml`` via the existing
``core.verification.rules.RuleEngine`` loader - this module never duplicates
that policy logic, it only asks the engine what is required and reconciles it
against what has actually been uploaded.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from config.settings import settings
from core.events.bus import EventBus
from core.logger.structured import get_logger
from core.verification.rules import RuleEngine
from database import db
from repositories import documents as documents_repo
from repositories import employees as employees_repo
from services.audit import AuditService

logger = get_logger(__name__)

# Rules.yaml only expresses a boolean "requires_background_check" per role - this is
# the document type we ask for when that flag is set, since the policy has no
# document name of its own to give us.
BACKGROUND_CHECK_DOCUMENT = "Background Check Consent"


class DocumentService:
    """Upload, checklist and status transitions for onboarding documents."""

    @staticmethod
    async def required_for(employee: Dict[str, Any]) -> List[str]:
        department = employee.get("department")
        role = employee.get("role")

        docs = set(RuleEngine.get_required_documents(department))
        if RuleEngine.requires_background_check(role):
            docs.add(BACKGROUND_CHECK_DOCUMENT)
        return sorted(docs)

    @staticmethod
    async def upload(
        *,
        employee_id: str,
        document_type: str,
        file_name: str,
        content: bytes,
        content_type: str,
        organization_id: Optional[str] = None,
        expiry_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        storage_path = f"{employee_id}/{uuid.uuid4()}_{file_name}"
        storage_url = await db.upload_file(
            settings.supabase_storage_bucket, storage_path, content, content_type
        )

        document = await documents_repo.create(
            {
                "organization_id": organization_id,
                "employee_id": employee_id,
                "document_type": document_type,
                "file_name": file_name,
                "file_type": content_type,
                "file_size": len(content),
                "storage_path": storage_path,
                "storage_url": storage_url,
                "status": "uploaded",
                "required": True,
                "expiry_date": expiry_date,
                "uploaded_at": datetime.utcnow().isoformat(),
            }
        )

        await AuditService.record(
            "document.uploaded",
            "document",
            document["id"],
            organization_id=organization_id,
        )

        try:
            await EventBus.publish(
                "DocumentUploaded",
                {"employee_id": employee_id, "document_id": document["id"], "document_type": document_type},
            )
        except Exception as exc:  # pragma: no cover
            logger.error("Failed to publish DocumentUploaded", exc_info=exc)

        await DocumentService._maybe_signal_complete(employee_id)
        return document

    @staticmethod
    async def _maybe_signal_complete(employee_id: str) -> None:
        """Fire EmployeeDocumentsSubmitted once every required document type is present."""
        employee = await employees_repo.get(employee_id)
        if not employee:
            return

        required = set(await DocumentService.required_for(employee))
        if not required:
            return

        uploaded_docs = await documents_repo.list_by_employee(employee_id)
        uploaded_types = {doc["document_type"] for doc in uploaded_docs if doc.get("status") != "rejected"}

        if required.issubset(uploaded_types):
            try:
                await EventBus.publish("EmployeeDocumentsSubmitted", {"employee_id": employee_id})
            except Exception as exc:  # pragma: no cover
                logger.error("Failed to publish EmployeeDocumentsSubmitted", exc_info=exc)

    @staticmethod
    async def list_for_employee(employee_id: str) -> List[Dict[str, Any]]:
        return await documents_repo.list_by_employee(employee_id)

    @staticmethod
    async def checklist(employee_id: str) -> List[Dict[str, Any]]:
        employee = await employees_repo.get(employee_id)
        required = await DocumentService.required_for(employee) if employee else []
        uploaded_docs = await documents_repo.list_by_employee(employee_id)
        by_type = {doc["document_type"]: doc for doc in uploaded_docs}

        items: List[Dict[str, Any]] = []
        seen = set()
        for document_type in required:
            seen.add(document_type)
            doc = by_type.get(document_type)
            items.append(
                {
                    "document_type": document_type,
                    "required": True,
                    "uploaded": doc is not None,
                    "status": doc.get("status") if doc else "pending",
                    "document_id": doc.get("id") if doc else None,
                }
            )

        # Include any extra documents the employee uploaded that weren't required.
        for document_type, doc in by_type.items():
            if document_type in seen:
                continue
            items.append(
                {
                    "document_type": document_type,
                    "required": False,
                    "uploaded": True,
                    "status": doc.get("status"),
                    "document_id": doc.get("id"),
                }
            )

        return items

    @staticmethod
    async def delete(document_id: str) -> bool:
        document = await documents_repo.get(document_id)
        if not document:
            return False

        if document.get("storage_path"):
            try:
                await db.delete_file(settings.supabase_storage_bucket, document["storage_path"])
            except Exception as exc:  # pragma: no cover
                logger.error("Failed to delete stored document file", exc_info=exc)

        deleted = await documents_repo.delete(document_id)
        if deleted:
            await AuditService.record("document.deleted", "document", document_id)
        return deleted

    @staticmethod
    async def set_status(
        document_id: str,
        status: str,
        verified_by: Optional[str] = None,
        errors: Optional[List[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        payload: Dict[str, Any] = {"status": status, "validation_errors": errors or []}
        if status == "verified":
            payload["verified_at"] = datetime.utcnow().isoformat()
            payload["verified_by"] = verified_by
        updated = await documents_repo.update(document_id, payload)
        await AuditService.record("document.status_changed", "document", document_id, changes={"status": status})
        return updated
