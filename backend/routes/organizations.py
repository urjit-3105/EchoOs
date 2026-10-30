"""Organization (tenant) management, including one-step org + admin setup."""

import re
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException

from core.logger.structured import get_logger
from core.verification.rules import RuleEngine
from repositories import approvals as approvals_repo
from repositories import documents as documents_repo
from repositories import employees as employees_repo
from repositories import invitations as invitations_repo
from repositories import notifications as notifications_repo
from repositories import organizations as organizations_repo
from repositories import workflows as workflows_repo
from routes.deps import get_optional_user
from schemas import OrganizationCreate, OrganizationResponse, OrganizationUpdate
from services.audit import AuditService
from services.auth import AuthService

logger = get_logger(__name__)

router = APIRouter(prefix="/organizations", tags=["Organizations"])


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
    return slug or "organization"


async def _unique_slug(base_slug: str) -> str:
    slug = base_slug
    suffix = 1
    while await organizations_repo.get_by_slug(slug):
        suffix += 1
        slug = f"{base_slug}-{suffix}"
    return slug


@router.get("/", response_model=List[OrganizationResponse])
async def list_organizations() -> List[Dict[str, Any]]:
    """List every organization."""
    return await organizations_repo.list(order_by="created_at")


@router.post("/", response_model=Dict[str, Any])
async def create_organization(
    payload: OrganizationCreate,
    admin_email: Optional[str] = None,
    admin_password: Optional[str] = None,
    admin_full_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Create an organization, seeding default compliance policies from ``config/rules.yaml``.

    When ``admin_email``/``admin_password`` are supplied, also creates the
    first admin user for the org in the same call.
    """
    base_slug = _slugify(payload.slug or payload.name)
    slug = await _unique_slug(base_slug)

    if not RuleEngine._rules:
        RuleEngine.load_rules()
    seeded_policies = dict(RuleEngine._rules or {})
    seeded_policies.update(payload.policies or {})

    org = await organizations_repo.create(
        {
            "name": payload.name,
            "slug": slug,
            "industry": payload.industry,
            "size": payload.size,
            "logo_url": payload.logo_url,
            "timezone": payload.timezone,
            "settings": payload.settings or {},
            "policies": seeded_policies,
        }
    )

    await AuditService.record(
        "organization.created",
        "organization",
        org["id"],
        organization_id=org["id"],
    )

    result: Dict[str, Any] = {"organization": org}

    if admin_email and admin_password:
        try:
            auth_result = await AuthService.register(
                email=admin_email,
                password=admin_password,
                full_name=admin_full_name or admin_email.split("@")[0],
                organization_id=org["id"],
                role="admin",
            )
            result["admin_user"] = auth_result["user"]
            result["access_token"] = auth_result["access_token"]
            result["token_type"] = auth_result["token_type"]
            await AuditService.record(
                "organization.admin_created",
                "organization",
                org["id"],
                organization_id=org["id"],
                actor=admin_email,
                actor_type="user",
            )
        except ValueError as exc:
            result["admin_user_error"] = str(exc)

    return result


@router.get("/current", response_model=Optional[OrganizationResponse])
async def current_organization(user: Optional[Dict[str, Any]] = Depends(get_optional_user)) -> Optional[Dict[str, Any]]:
    """The caller's organization, else the first organization. Never 500s when none exists."""
    org = None
    if user and user.get("organization_id"):
        org = await organizations_repo.get(user["organization_id"])
    if not org:
        org = await organizations_repo.get_default()
    return org


@router.get("/{organization_id}", response_model=OrganizationResponse)
async def get_organization(organization_id: str) -> Dict[str, Any]:
    """Fetch one organization by id."""
    org = await organizations_repo.get(organization_id)
    if not org:
        raise HTTPException(status_code=404, detail=f"Organization '{organization_id}' not found.")
    return org


@router.patch("/{organization_id}", response_model=OrganizationResponse)
async def update_organization(organization_id: str, payload: OrganizationUpdate) -> Dict[str, Any]:
    """Patch organization fields (name, settings, policies, ...)."""
    existing = await organizations_repo.get(organization_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Organization '{organization_id}' not found.")

    updates = {key: value for key, value in payload.model_dump(exclude_unset=True).items()}
    updated = await organizations_repo.update(organization_id, updates) if updates else existing

    await AuditService.record(
        "organization.updated",
        "organization",
        organization_id,
        organization_id=organization_id,
        changes=updates,
    )
    return updated or existing


@router.get("/{organization_id}/stats")
async def organization_stats(organization_id: str) -> Dict[str, Any]:
    """Dashboard aggregates: employee counts, workflow counts, pending approvals/documents, recent activity."""
    org = await organizations_repo.get(organization_id)
    if not org:
        raise HTTPException(status_code=404, detail=f"Organization '{organization_id}' not found.")

    employees_by_status = await employees_repo.count_by_status(organization_id)
    total_employees = sum(employees_by_status.values())

    workflow_rows = await workflows_repo.list(organization_id=organization_id)
    workflows_by_status: Dict[str, int] = {}
    for row in workflow_rows:
        status = row.get("status") or "unknown"
        workflows_by_status[status] = workflows_by_status.get(status, 0) + 1

    pending_approvals = await approvals_repo.list_pending(organization_id)
    pending_invitations = await invitations_repo.list_pending(organization_id)

    document_rows = await documents_repo.list(organization_id=organization_id)
    documents_pending = [doc for doc in document_rows if doc.get("status") in ("uploaded", "pending")]

    recent_activity = await AuditService.recent(organization_id, limit=20)

    return {
        "organization_id": organization_id,
        "total_employees": total_employees,
        "employees_by_status": employees_by_status,
        "workflows_by_status": workflows_by_status,
        "active_workflows": sum(
            count for status, count in workflows_by_status.items() if status in ("pending", "running", "paused")
        ),
        "completed_workflows": workflows_by_status.get("completed", 0),
        "failed_workflows": workflows_by_status.get("failed", 0),
        "pending_approvals": len(pending_approvals),
        "pending_invitations": len(pending_invitations),
        "documents_pending_review": len(documents_pending),
        "recent_activity": recent_activity,
    }
