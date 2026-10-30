"""Thin event-wiring layer between the event bus and the workflow orchestrator.

The actual state machine lives in ``core.workflow.orchestration.OnboardingOrchestrator``
(owned by another engineer). This module only:

1. Subscribes to the events that should kick off or acknowledge onboarding.
2. Exposes a ``start`` delegate so routes/services don't need to know the
   orchestrator's import path (and so importing this module never fails even
   if the orchestrator hasn't landed yet).
3. Builds the portal-facing progress summary employees see while they wait.
"""

from typing import Any, Dict, Optional

from core.events.bus import EventBus
from core.logger.structured import get_logger
from repositories import employees as employees_repo
from repositories import workflows as workflows_repo
from services.audit import AuditService
from services.documents import DocumentService
from services.notifications import NotificationService

logger = get_logger(__name__)


class OnboardingService:
    """Event wiring + portal progress summary. Orchestration itself lives in core/."""

    @staticmethod
    async def register_event_handlers() -> None:
        """Wire the two events onboarding cares about. Call once at app startup."""
        EventBus.subscribe("EmployeeDocumentsSubmitted", OnboardingService._on_documents_submitted)
        EventBus.subscribe("InvitationAccepted", OnboardingService._on_invitation_accepted)
        logger.info("Onboarding event handlers registered")

    @staticmethod
    async def _on_documents_submitted(payload: Dict[str, Any]) -> None:
        employee_id = payload.get("employee_id")
        if not employee_id:
            logger.warning("EmployeeDocumentsSubmitted received without employee_id", context={"payload": payload})
            return

        active = await workflows_repo.get_active_for_employee(employee_id)
        if active:
            logger.info(
                "Workflow already active for employee; skipping duplicate start",
                context={"employee_id": employee_id, "workflow_id": active.get("id")},
            )
            return

        try:
            await OnboardingService.start(employee_id)
        except Exception as exc:  # pragma: no cover - event handlers must not crash the bus
            logger.error("Failed to start onboarding workflow", context={"employee_id": employee_id}, exc_info=exc)

    @staticmethod
    async def _on_invitation_accepted(payload: Dict[str, Any]) -> None:
        employee_id = payload.get("employee_id")
        try:
            await NotificationService.push(
                type="success",
                title="Invitation accepted",
                message="The employee accepted their invitation and can now complete their profile.",
                category="invitation",
                organization_id=payload.get("organization_id"),
                employee_id=employee_id,
            )
            await AuditService.record(
                "invitation.accepted.acknowledged",
                "employee",
                employee_id or "unknown",
                organization_id=payload.get("organization_id"),
            )
        except Exception as exc:  # pragma: no cover
            logger.error("Failed to acknowledge InvitationAccepted", exc_info=exc)

    @staticmethod
    async def start(employee_id: str, template_key: Optional[str] = None) -> Dict[str, Any]:
        """Delegate to the orchestrator. Imported lazily to dodge a core <-> services circular import."""
        try:
            from core.workflow.orchestration import OnboardingOrchestrator
        except ImportError as exc:
            raise RuntimeError(
                "core.workflow.orchestration.OnboardingOrchestrator is not available yet. "
                "The orchestrator module must exist before onboarding workflows can start."
            ) from exc

        return await OnboardingOrchestrator.start_for_employee(employee_id, template_key)

    @staticmethod
    async def progress(employee_id: str) -> Dict[str, Any]:
        """Portal-facing summary of where an employee is in the onboarding journey."""
        employee = await employees_repo.get(employee_id)
        if not employee:
            raise ValueError(f"Employee '{employee_id}' not found.")

        checklist = await DocumentService.checklist(employee_id)
        workflow = await workflows_repo.get_active_for_employee(employee_id)
        if not workflow:
            workflows = await workflows_repo.list_by_employee(employee_id)
            workflow = workflows[0] if workflows else None

        required_items = [item for item in checklist if item["required"]]
        uploaded_required = [item for item in required_items if item["uploaded"]]

        steps_total = 4  # invitation, profile, documents, terms
        steps_done = 0
        invitation_accepted = employee.get("status") not in (None, "invited")
        if invitation_accepted:
            steps_done += 1
        profile_completed = bool(employee.get("profile_completed"))
        if profile_completed:
            steps_done += 1
        if required_items and len(uploaded_required) == len(required_items):
            steps_done += 1
        terms_accepted = employee.get("terms_accepted_at") is not None
        if terms_accepted:
            steps_done += 1

        if workflow:
            percent_complete = int(workflow.get("progress") or 0)
            current_stage = workflow.get("current_stage")
            status = workflow.get("status")
        else:
            percent_complete = int((steps_done / steps_total) * 100) if steps_total else 0
            current_stage = "documents" if not required_items or len(uploaded_required) < len(required_items) else "awaiting_workflow"
            status = employee.get("status")

        return {
            "invitation_accepted": invitation_accepted,
            "profile_completed": profile_completed,
            "documents": checklist,
            "terms_accepted": terms_accepted,
            "workflow": workflow,
            "percent_complete": percent_complete,
            "current_stage": current_stage,
            "status": status,
        }
