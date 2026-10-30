"""Employee CRUD, profile completion, timeline and onboarding kickoff."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException

from core.events.bus import EventBus
from core.logger.structured import get_logger
from repositories import audit_logs
from repositories import documents as documents_repo
from repositories import employees as employees_repo
from repositories import execution_logs as execution_logs_repo
from repositories import workflows as workflows_repo
from routes.deps import PaginationParams
from schemas import EmployeeCreate, EmployeeResponse, EmployeeUpdate, ProfileCompletionRequest
from services.audit import AuditService
from services.notifications import NotificationService
from services.onboarding import OnboardingService

logger = get_logger(__name__)

router = APIRouter(prefix="/employees", tags=["Employees"])


@router.get("/")
async def list_employees(
    organization_id: Optional[str] = None,
    status: Optional[str] = None,
    department: Optional[str] = None,
    search: Optional[str] = None,
    pagination: PaginationParams = Depends(),
) -> Dict[str, Any]:
    """List employees with optional filters and case-insensitive name/email search."""
    filters: Dict[str, Any] = {}
    if organization_id:
        filters["organization_id"] = organization_id
    if status:
        filters["status"] = status
    if department:
        filters["department"] = department

    rows = await employees_repo.list(order_by="created_at", descending=True, **filters)

    if search:
        needle = search.lower().strip()
        rows = [
            row
            for row in rows
            if needle in f"{row.get('first_name', '')} {row.get('last_name', '')}".lower()
            or needle in (row.get("email") or "").lower()
        ]

    total = len(rows)
    page = rows[pagination.offset : pagination.offset + pagination.limit]
    return {"items": page, "total": total, "limit": pagination.limit, "offset": pagination.offset}


@router.get("/stats")
async def employee_stats(organization_id: Optional[str] = None) -> Dict[str, Any]:
    """Employee counts by status - MUST be declared before /{employee_id}."""
    counts = await employees_repo.count_by_status(organization_id)
    return {"total": sum(counts.values()), "by_status": counts}


@router.post("/", response_model=EmployeeResponse)
async def create_employee(payload: EmployeeCreate) -> Dict[str, Any]:
    """Create an employee record directly (outside the invitation flow)."""
    existing = await employees_repo.get_by_email(payload.email)
    if existing:
        raise HTTPException(status_code=400, detail=f"An employee with email '{payload.email}' already exists.")

    data = payload.model_dump(exclude_unset=True)
    employee = await employees_repo.create(data)
    await AuditService.record(
        "employee.created", "employee", employee["id"], organization_id=employee.get("organization_id")
    )
    return employee


@router.get("/{employee_id}")
async def get_employee(employee_id: str) -> Dict[str, Any]:
    """Employee record + documents + workflows + onboarding progress."""
    employee = await employees_repo.get(employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail=f"Employee '{employee_id}' not found.")

    documents = await documents_repo.list_by_employee(employee_id)
    workflows = await workflows_repo.list_by_employee(employee_id)

    try:
        progress = await OnboardingService.progress(employee_id)
    except ValueError:
        progress = None

    return {
        "employee": employee,
        "documents": documents,
        "workflows": workflows,
        "progress": progress,
    }


@router.patch("/{employee_id}", response_model=EmployeeResponse)
async def update_employee(employee_id: str, payload: EmployeeUpdate) -> Dict[str, Any]:
    """Patch employee fields."""
    existing = await employees_repo.get(employee_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Employee '{employee_id}' not found.")

    updates = payload.model_dump(exclude_unset=True)
    updated = await employees_repo.update(employee_id, updates) if updates else existing

    await AuditService.record(
        "employee.updated",
        "employee",
        employee_id,
        organization_id=existing.get("organization_id"),
        changes=updates,
    )
    return updated or existing


@router.delete("/{employee_id}")
async def delete_employee(employee_id: str) -> Dict[str, Any]:
    """Delete an employee record."""
    existing = await employees_repo.get(employee_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Employee '{employee_id}' not found.")

    deleted = await employees_repo.delete(employee_id)
    if deleted:
        await AuditService.record(
            "employee.deleted", "employee", employee_id, organization_id=existing.get("organization_id")
        )
    return {"message": "Employee deleted." if deleted else "Employee could not be deleted.", "success": deleted}


@router.post("/{employee_id}/profile")
async def complete_profile(employee_id: str, payload: ProfileCompletionRequest) -> Dict[str, Any]:
    """Complete the employee's profile from the self-service portal."""
    employee = await employees_repo.get(employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail=f"Employee '{employee_id}' not found.")

    merged_profile = dict(employee.get("profile") or {})
    merged_profile.update(payload.profile or {})

    updates: Dict[str, Any] = {"profile": merged_profile, "profile_completed": True}
    if payload.phone:
        updates["phone"] = payload.phone
    if payload.accept_terms:
        updates["terms_accepted_at"] = datetime.utcnow().isoformat()

    updated = await employees_repo.update(employee_id, updates)

    await AuditService.record(
        "employee.profile_completed",
        "employee",
        employee_id,
        organization_id=employee.get("organization_id"),
    )
    await NotificationService.push(
        type="success",
        title="Profile completed",
        message=f"{employee.get('first_name', '')} {employee.get('last_name', '')} completed their profile.".strip(),
        category="employee",
        organization_id=employee.get("organization_id"),
        employee_id=employee_id,
    )
    try:
        await EventBus.publish("EmployeeProfileCompleted", {"employee_id": employee_id})
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to publish EmployeeProfileCompleted", exc_info=exc)

    return updated or employee


@router.get("/{employee_id}/timeline")
async def employee_timeline(employee_id: str) -> List[Dict[str, Any]]:
    """Merged audit-log + execution-log history across the employee's workflows."""
    employee = await employees_repo.get(employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail=f"Employee '{employee_id}' not found.")

    entries: List[Dict[str, Any]] = []

    for row in await AuditService.list_for("employee", employee_id):
        entries.append({"source": "audit_log", "timestamp": row.get("timestamp"), **row})

    workflows = await workflows_repo.list_by_employee(employee_id)
    for workflow in workflows:
        workflow_id = workflow["id"]
        for row in await audit_logs.list_for_resource("workflow", workflow_id):
            entries.append({"source": "audit_log", "timestamp": row.get("timestamp"), **row})
        for row in await execution_logs_repo.list_by_workflow(workflow_id):
            entries.append({"source": "execution_log", "timestamp": row.get("timestamp"), **row})

    entries.sort(key=lambda entry: entry.get("timestamp") or "")
    return entries


@router.post("/{employee_id}/start-onboarding")
async def start_onboarding(employee_id: str, template_key: Optional[str] = None) -> Dict[str, Any]:
    """Kick off the onboarding workflow for this employee."""
    employee = await employees_repo.get(employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail=f"Employee '{employee_id}' not found.")

    active = await workflows_repo.get_active_for_employee(employee_id)
    if active:
        raise HTTPException(status_code=400, detail=f"Employee already has an active workflow '{active['id']}'.")

    try:
        workflow = await OnboardingService.start(employee_id, template_key)
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"workflow": workflow}
