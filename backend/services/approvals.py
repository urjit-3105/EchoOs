"""Human-in-the-loop approval gate service.

Backs the ``compliance_approval`` step in ``employee_onboarding.yaml`` (and any
other workflow step with ``requires_approval: true``). Persists the approval,
notifies the right humans by email + in-app notification, and republishes
resolution as ``ApprovalResolved`` so the orchestrator can resume the workflow.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from config.settings import settings
from core.events.bus import EventBus
from core.logger.structured import get_logger
from repositories import approvals as approvals_repo
from repositories import users as users_repo
from services.audit import AuditService
from services.email import EmailService
from services.notifications import NotificationService

logger = get_logger(__name__)


class ApprovalService:
    """Create, notify, resolve and escalate approval requests."""

    @staticmethod
    def _approval_url(approval_id: str) -> str:
        return f"{settings.frontend_url}/approvals/{approval_id}"

    @staticmethod
    async def _approvers(organization_id: Optional[str], required_role: str) -> List[Dict[str, Any]]:
        filters: Dict[str, Any] = {"role": required_role}
        if organization_id:
            filters["organization_id"] = organization_id
        approvers = await users_repo.list(**filters)
        if approvers:
            return approvers

        # Fall back to org admins when nobody holds the required role.
        admin_filters: Dict[str, Any] = {"role": "admin"}
        if organization_id:
            admin_filters["organization_id"] = organization_id
        return await users_repo.list(**admin_filters)

    @staticmethod
    async def request(
        *,
        workflow_id: str,
        task_id: str,
        title: str,
        description: str,
        reason: str,
        employee_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        required_role: str = "hr",
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        expires_at = datetime.utcnow() + timedelta(seconds=settings.escalation_timeout_seconds)

        approval = await approvals_repo.create(
            {
                "organization_id": organization_id,
                "workflow_id": workflow_id,
                "task_id": task_id,
                "employee_id": employee_id,
                "title": title,
                "description": description,
                "reason": reason,
                "status": "pending",
                "required_role": required_role,
                "payload": payload or {},
                "expires_at": expires_at.isoformat(),
            }
        )

        await ApprovalService._notify_approvers(approval, is_reminder=False)

        await AuditService.record(
            "approval.requested",
            "approval",
            approval["id"],
            organization_id=organization_id,
        )
        return approval

    @staticmethod
    async def _notify_approvers(approval: Dict[str, Any], is_reminder: bool) -> None:
        approvers = await ApprovalService._approvers(approval.get("organization_id"), approval.get("required_role", "hr"))
        approval_url = ApprovalService._approval_url(approval["id"])
        employee_name = approval.get("title", "an employee")

        for approver in approvers:
            approver_name = approver.get("full_name") or approver.get("email", "there")
            if is_reminder:
                subject, html = EmailService.approval_reminder_email(
                    approver_name, employee_name, approval_url, approval.get("reason", "")
                )
            else:
                subject, html = EmailService.approval_request_email(
                    approver_name, employee_name, approval_url, approval.get("reason", "")
                )
            await EmailService.send(to=approver["email"], subject=subject, html=html, template="approval_request")

        await NotificationService.push(
            type="approval",
            title="Approval requested" if not is_reminder else "Approval reminder",
            message=approval.get("description") or approval.get("title", ""),
            category="approval",
            organization_id=approval.get("organization_id"),
            employee_id=approval.get("employee_id"),
            workflow_id=approval.get("workflow_id"),
            action_url=approval_url,
        )

    @staticmethod
    async def resolve(
        approval_id: str,
        *,
        approved: bool,
        approver_email: Optional[str] = None,
        approver_id: Optional[str] = None,
        comments: Optional[str] = None,
    ) -> Dict[str, Any]:
        approval = await approvals_repo.get(approval_id)
        if not approval:
            raise ValueError(f"Approval '{approval_id}' not found.")

        updated = await approvals_repo.update(
            approval_id,
            {
                "status": "approved" if approved else "rejected",
                "approver_email": approver_email,
                "approver_id": approver_id,
                "comments": comments,
                "resolved_at": datetime.utcnow().isoformat(),
            },
        )
        updated = updated or approval

        await AuditService.record(
            "approval.resolved",
            "approval",
            approval_id,
            actor=approver_email,
            actor_type="user",
            organization_id=approval.get("organization_id"),
            changes={"approved": approved, "comments": comments},
        )

        await NotificationService.push(
            type="success" if approved else "warning",
            title="Approval granted" if approved else "Approval rejected",
            message=updated.get("title", ""),
            category="approval",
            organization_id=approval.get("organization_id"),
            employee_id=approval.get("employee_id"),
            workflow_id=approval.get("workflow_id"),
        )

        try:
            await EventBus.publish(
                "ApprovalResolved",
                {
                    "workflow_id": approval.get("workflow_id"),
                    "task_id": approval.get("task_id"),
                    "approved": approved,
                },
            )
        except Exception as exc:  # pragma: no cover
            logger.error("Failed to publish ApprovalResolved", exc_info=exc)

        return updated

    @staticmethod
    async def send_reminder(approval: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            await ApprovalService._notify_approvers(approval, is_reminder=True)
            updated = await approvals_repo.update(
                approval["id"],
                {
                    "reminder_count": int(approval.get("reminder_count") or 0) + 1,
                    "last_reminder_at": datetime.utcnow().isoformat(),
                },
            )
            await AuditService.record("approval.reminder_sent", "approval", approval["id"])
            return updated
        except Exception as exc:  # pragma: no cover - scheduler must keep running
            logger.error("Failed to send approval reminder", context={"approval_id": approval.get("id")}, exc_info=exc)
            return None

    @staticmethod
    async def escalate(approval: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            updated = await approvals_repo.update(
                approval["id"],
                {"status": "escalated", "escalated_at": datetime.utcnow().isoformat()},
            )
            await NotificationService.push(
                type="error",
                title="Approval escalated",
                message=f"Approval '{approval.get('title', approval['id'])}' has exceeded the escalation window.",
                category="approval",
                organization_id=approval.get("organization_id"),
                employee_id=approval.get("employee_id"),
                workflow_id=approval.get("workflow_id"),
            )
            await AuditService.record("approval.escalated", "approval", approval["id"])
            return updated
        except Exception as exc:  # pragma: no cover - scheduler must keep running
            logger.error("Failed to escalate approval", context={"approval_id": approval.get("id")}, exc_info=exc)
            return None

    @staticmethod
    async def list_pending(org_id: Optional[str] = None) -> List[Dict[str, Any]]:
        return await approvals_repo.list_pending(org_id)

    @staticmethod
    async def get(approval_id: str) -> Optional[Dict[str, Any]]:
        return await approvals_repo.get(approval_id)
