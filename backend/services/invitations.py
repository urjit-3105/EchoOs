"""Invitation lifecycle: create, resend, accept, revoke, expire.

This is the entry point into the whole onboarding flow - accepting an
invitation is what eventually lets an employee reach the document upload step
that fires ``EmployeeDocumentsSubmitted`` and starts the workflow.
"""

import base64
import io
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from config.settings import settings
from core.events.bus import EventBus
from core.logger.structured import get_logger
from repositories import employees as employees_repo
from repositories import invitations as invitations_repo
from repositories import organizations as organizations_repo
from services.audit import AuditService
from services.email import EmailService
from services.notifications import NotificationService

logger = get_logger(__name__)


class InvitationService:
    """Creates and resolves employee invitations."""

    @staticmethod
    def accept_url(token: str) -> str:
        return f"{settings.frontend_url}/portal/{token}"

    @staticmethod
    def qr_code_data_url(url: str) -> str:
        """Best-effort QR code as a base64 PNG data URL. Empty string if ``qrcode`` is unavailable."""
        try:
            import qrcode
        except ImportError:  # pragma: no cover - optional dependency
            logger.warning("qrcode package not installed; skipping QR code generation")
            return ""

        try:
            img = qrcode.make(url)
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            encoded = base64.b64encode(buffer.getvalue()).decode()
            return f"data:image/png;base64,{encoded}"
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Failed to render QR code", exc_info=exc)
            return ""

    @staticmethod
    async def create(
        *,
        email: str,
        first_name: str,
        last_name: str,
        organization_id: str,
        role: str = "employee",
        department: Optional[str] = None,
        job_title: Optional[str] = None,
        invited_by: Optional[str] = None,
        message: Optional[str] = None,
    ) -> Dict[str, Any]:
        email = email.lower().strip()

        employee = await employees_repo.get_by_email(email)
        if not employee:
            employee = await employees_repo.create(
                {
                    "organization_id": organization_id,
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": email,
                    "department": department,
                    "role": role,
                    "job_title": job_title,
                    "status": "invited",
                }
            )

        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=settings.invitation_expiry_hours)

        invitation = await invitations_repo.create(
            {
                "organization_id": organization_id,
                "employee_id": employee["id"],
                "email": email,
                "token": token,
                "role": role,
                "department": department,
                "job_title": job_title,
                "status": "pending",
                "invited_by": invited_by,
                "message": message,
                "expires_at": expires_at.isoformat(),
            }
        )

        accept_url = InvitationService.accept_url(token)
        qr_code = InvitationService.qr_code_data_url(accept_url)

        org = await organizations_repo.get(organization_id)
        org_name = org.get("name") if org else settings.app_name

        subject, html = EmailService.invitation_email(
            employee_name=f"{first_name} {last_name}".strip(),
            org_name=org_name,
            accept_url=accept_url,
            expires_at=expires_at.isoformat(),
        )
        await EmailService.send(to=email, subject=subject, html=html, template="invitation")

        await AuditService.record(
            "invitation.created",
            "invitation",
            invitation["id"],
            actor=invited_by,
            actor_type="user" if invited_by else "system",
            organization_id=organization_id,
        )
        await NotificationService.push(
            type="info",
            title="Invitation sent",
            message=f"Invited {first_name} {last_name} ({email})",
            category="invitation",
            organization_id=organization_id,
            employee_id=employee["id"],
        )

        try:
            await EventBus.publish(
                "EmployeeInvited",
                {"employee_id": employee["id"], "invitation_id": invitation["id"], "email": email},
            )
        except Exception as exc:  # pragma: no cover
            logger.error("Failed to publish EmployeeInvited", exc_info=exc)

        return {
            "invitation": invitation,
            "employee": employee,
            "accept_url": accept_url,
            "qr_code": qr_code,
        }

    @staticmethod
    async def get_by_token(token: str) -> Optional[Dict[str, Any]]:
        invitation = await invitations_repo.get_by_token(token)
        if not invitation:
            return None

        if invitation.get("status") == "pending" and InvitationService._is_expired(invitation):
            invitation = await invitations_repo.mark_expired(invitation["id"]) or invitation

        employee = None
        if invitation.get("employee_id"):
            employee = await employees_repo.get(invitation["employee_id"])

        organization = None
        if invitation.get("organization_id"):
            organization = await organizations_repo.get(invitation["organization_id"])

        return {"invitation": invitation, "employee": employee, "organization": organization}

    @staticmethod
    def _is_expired(invitation: Dict[str, Any]) -> bool:
        expires_at = invitation.get("expires_at")
        if not expires_at:
            return False
        try:
            expiry = datetime.fromisoformat(str(expires_at).replace("Z", ""))
        except ValueError:
            return False
        return datetime.utcnow() > expiry

    @staticmethod
    async def accept(
        token: str, *, password: Optional[str] = None, profile: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        bundle = await InvitationService.get_by_token(token)
        if not bundle or not bundle.get("invitation"):
            raise ValueError("Invitation not found.")

        invitation = bundle["invitation"]
        if invitation.get("status") == "revoked":
            raise ValueError("This invitation has been revoked.")
        if invitation.get("status") == "expired" or InvitationService._is_expired(invitation):
            raise ValueError("This invitation has expired.")
        if invitation.get("status") == "accepted":
            raise ValueError("This invitation has already been accepted.")

        employee = bundle.get("employee")
        if not employee:
            raise ValueError("No employee record linked to this invitation.")

        update_payload: Dict[str, Any] = {"status": "accepted"}
        if profile:
            merged_profile = dict(employee.get("profile") or {})
            merged_profile.update(profile)
            update_payload["profile"] = merged_profile
            update_payload["profile_completed"] = True
        employee = await employees_repo.update(employee["id"], update_payload) or employee

        invitation = await invitations_repo.mark_accepted(invitation["id"]) or invitation

        from services.auth import AuthService

        user = await AuthService.ensure_user_for_employee(
            employee, password=password, role=invitation.get("role", "employee")
        )

        await AuditService.record(
            "invitation.accepted",
            "invitation",
            invitation["id"],
            actor=employee.get("email"),
            actor_type="user",
            organization_id=invitation.get("organization_id"),
        )

        try:
            await EventBus.publish(
                "InvitationAccepted",
                {
                    "employee_id": employee["id"],
                    "invitation_id": invitation["id"],
                    "organization_id": invitation.get("organization_id"),
                },
            )
        except Exception as exc:  # pragma: no cover
            logger.error("Failed to publish InvitationAccepted", exc_info=exc)

        return {"invitation": invitation, "employee": employee, "user": user}

    @staticmethod
    async def resend(invitation_id: str) -> Optional[Dict[str, Any]]:
        invitation = await invitations_repo.get(invitation_id)
        if not invitation:
            return None

        employee = None
        if invitation.get("employee_id"):
            employee = await employees_repo.get(invitation["employee_id"])

        accept_url = InvitationService.accept_url(invitation["token"])
        org = await organizations_repo.get(invitation["organization_id"]) if invitation.get("organization_id") else None
        org_name = org.get("name") if org else settings.app_name
        employee_name = f"{employee.get('first_name', '')} {employee.get('last_name', '')}".strip() if employee else invitation["email"]

        subject, html = EmailService.invitation_email(
            employee_name=employee_name,
            org_name=org_name,
            accept_url=accept_url,
            expires_at=invitation.get("expires_at", ""),
        )
        await EmailService.send(to=invitation["email"], subject=subject, html=html, template="invitation_reminder")

        updated = await invitations_repo.update(
            invitation_id,
            {
                "reminder_count": int(invitation.get("reminder_count") or 0) + 1,
                "last_reminder_at": datetime.utcnow().isoformat(),
            },
        )
        await AuditService.record("invitation.resent", "invitation", invitation_id)
        return updated

    @staticmethod
    async def revoke(invitation_id: str) -> Optional[Dict[str, Any]]:
        updated = await invitations_repo.update(invitation_id, {"status": "revoked"})
        await AuditService.record("invitation.revoked", "invitation", invitation_id)
        return updated

    @staticmethod
    async def expire_stale() -> int:
        """Bulk-expire pending invitations past ``expires_at`` - called by the scheduler."""
        pending = await invitations_repo.list_pending()
        expired = 0
        for invitation in pending:
            if InvitationService._is_expired(invitation):
                await invitations_repo.mark_expired(invitation["id"])
                expired += 1
        if expired:
            logger.info("Expired stale invitations", context={"count": expired})
        return expired
