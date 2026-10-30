"""Employee self-service portal - fully public, the invitation token IS the credential.

Every endpoint resolves the invitation via ``InvitationService.get_by_token``
and 404s (unknown token) or 410s (expired/revoked invitation) before touching
anything else.
"""

from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, File, HTTPException, UploadFile

from core.events.bus import EventBus
from core.logger.structured import get_logger
from core.verification.rules import RuleEngine
from repositories import documents as documents_repo
from repositories import employees as employees_repo
from repositories import organizations as organizations_repo
from repositories import workflows as workflows_repo
from services.documents import DocumentService
from services.invitations import InvitationService
from services.onboarding import OnboardingService

logger = get_logger(__name__)

router = APIRouter(prefix="/portal", tags=["Employee Portal"])


async def _resolve(token: str) -> Dict[str, Any]:
    bundle = await InvitationService.get_by_token(token)
    if not bundle or not bundle.get("invitation"):
        raise HTTPException(status_code=404, detail="Invitation not found.")

    status = bundle["invitation"].get("status")
    if status in ("expired", "revoked"):
        raise HTTPException(status_code=410, detail=f"This invitation has been {status}.")
    if not bundle.get("employee"):
        raise HTTPException(status_code=404, detail="No employee record linked to this invitation.")
    return bundle


@router.get("/{token}")
async def portal_summary(token: str) -> Dict[str, Any]:
    """Invitation + employee + organization summary."""
    return await _resolve(token)


@router.get("/{token}/progress")
async def portal_progress(token: str) -> Dict[str, Any]:
    """Onboarding progress summary for the progress tracker."""
    bundle = await _resolve(token)
    return await OnboardingService.progress(bundle["employee"]["id"])


@router.post("/{token}/profile")
async def portal_save_profile(token: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Save profile fields submitted from the portal and mark the profile complete."""
    bundle = await _resolve(token)
    employee = bundle["employee"]

    profile_fields = payload.get("profile", payload)
    merged_profile = dict(employee.get("profile") or {})
    merged_profile.update(profile_fields or {})

    updates: Dict[str, Any] = {"profile": merged_profile, "profile_completed": True}
    if payload.get("phone"):
        updates["phone"] = payload["phone"]

    updated = await employees_repo.update(employee["id"], updates)

    try:
        await EventBus.publish("EmployeeProfileCompleted", {"employee_id": employee["id"]})
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to publish EmployeeProfileCompleted", exc_info=exc)

    return updated or employee


@router.get("/{token}/documents")
async def portal_documents(token: str) -> List[Dict[str, Any]]:
    """The employee's document checklist."""
    bundle = await _resolve(token)
    return await DocumentService.checklist(bundle["employee"]["id"])


@router.post("/{token}/documents")
async def portal_upload_document(
    token: str,
    document_type: str,
    file: UploadFile = File(...),
) -> Dict[str, Any]:
    """Upload a document for the invited employee."""
    bundle = await _resolve(token)
    employee = bundle["employee"]

    content = await file.read()
    return await DocumentService.upload(
        employee_id=employee["id"],
        document_type=document_type,
        file_name=file.filename or document_type,
        content=content,
        content_type=file.content_type or "application/octet-stream",
        organization_id=employee.get("organization_id"),
    )


@router.delete("/{token}/documents/{document_id}")
async def portal_delete_document(token: str, document_id: str) -> Dict[str, Any]:
    """Delete a document the employee previously uploaded."""
    bundle = await _resolve(token)
    document = await documents_repo.get(document_id)
    if not document or document.get("employee_id") != bundle["employee"]["id"]:
        raise HTTPException(status_code=404, detail=f"Document '{document_id}' not found for this invitation.")

    deleted = await DocumentService.delete(document_id)
    return {"message": "Document deleted." if deleted else "Document could not be deleted.", "success": deleted}


@router.get("/{token}/policies")
async def portal_policies(token: str) -> Dict[str, Any]:
    """Organization policies + rules.yaml requirements rendered as readable items."""
    bundle = await _resolve(token)
    employee = bundle["employee"]
    organization = bundle.get("organization") or {}

    if not RuleEngine._rules:
        RuleEngine.load_rules()

    required_documents = RuleEngine.get_required_documents(employee.get("department"))
    required_profile_fields = RuleEngine.get_required_profile_fields()
    background_check = RuleEngine.requires_background_check(employee.get("role"))

    items = [f"You must submit: {doc}" for doc in required_documents]
    items.append(f"Your profile must include: {', '.join(required_profile_fields)}")
    if background_check:
        items.append("Your role requires a background check consent form.")

    return {
        "organization_policies": organization.get("policies") or {},
        "requirements": items,
    }


@router.post("/{token}/accept-terms")
async def portal_accept_terms(token: str) -> Dict[str, Any]:
    """Record that the employee reviewed policies and accepted terms."""
    bundle = await _resolve(token)
    employee = bundle["employee"]
    now = datetime.utcnow().isoformat()
    updated = await employees_repo.update(
        employee["id"], {"terms_accepted_at": now, "policies_reviewed_at": now}
    )
    return updated or employee


@router.get("/{token}/workflow")
async def portal_workflow(token: str) -> Dict[str, Any]:
    """Live workflow status for the progress tracker."""
    bundle = await _resolve(token)
    employee_id = bundle["employee"]["id"]
    workflow = await workflows_repo.get_active_for_employee(employee_id)
    if not workflow:
        workflows = await workflows_repo.list_by_employee(employee_id)
        workflow = workflows[0] if workflows else None
    return {"workflow": workflow}
