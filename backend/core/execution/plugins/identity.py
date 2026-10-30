"""IdentityPlugin - provisions the internal corporate identity for a new hire.

Unlike the other plugins this one has no third-party equivalent to fall back
to: an employee number, a corporate email and a login account are first-party
records in our own database, so this plugin is always "live" - "simulated"
would just mean "onboarding silently did nothing", which defeats the point.
"""

import re
import secrets
from datetime import datetime
from typing import Any, Dict, List, Optional

from core.execution.plugins.base import BasePlugin
from core.execution.registry import ToolRegistry
from core.logger.structured import get_logger

logger = get_logger(__name__)


def _slugify(value: Optional[str]) -> str:
    """Lowercase, alphanumeric-only slug used for corporate email local-parts and domains."""
    return re.sub(r"[^a-zA-Z0-9]+", "", value or "").lower()


def _groups_for_department(department: Optional[str]) -> List[str]:
    """Static department -> group-membership mapping, shared by create_account and assign_groups."""
    key = (department or "").strip().lower()
    if key == "engineering":
        return ["eng-all", "github", "vpn"]
    if key == "sales":
        return ["sales-all", "crm"]
    return ["all-staff"]


@ToolRegistry.register("identity")
class IdentityPlugin(BasePlugin):
    """Provisions the corporate account, employee number and group memberships for a new hire."""

    @property
    def tool_name(self) -> str:
        return "identity"

    async def connect(self) -> bool:
        return True

    async def validate(self, inputs: Dict[str, Any]) -> bool:
        return bool(inputs.get("employee_id"))

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        action = inputs.get("action", "create_account")
        try:
            if action == "activate_account":
                result = await self._activate(inputs)
            elif action == "deactivate_account":
                result = await self._deactivate(inputs)
            elif action == "assign_groups":
                result = await self._assign_groups(inputs)
            else:
                result = await self._create_account(inputs)
            await self._audit(action, inputs, result)
            return result
        except Exception as exc:
            logger.error("Identity plugin execution failed", context={"action": action}, exc_info=exc)
            result = {"status": "failed", "mode": "live", "error": str(exc)}
            await self._audit(action, inputs, result)
            return result

    async def rollback(self, execution_data: Dict[str, Any]) -> bool:
        employee_id = execution_data.get("employee_id")
        if not employee_id:
            return True
        result = await self._deactivate({"employee_id": employee_id})
        return result.get("status") == "success"

    async def health(self) -> bool:
        return True  # internal to our own database - always considered healthy

    # ------------------------------------------------------------------
    async def _create_account(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        from repositories import employees as employees_repo
        from repositories import organizations as organizations_repo
        from repositories import users as users_repo
        from services.auth import AuthService

        employee_id = inputs["employee_id"]
        employee = await employees_repo.get(employee_id)
        if not employee:
            return {"status": "failed", "mode": "live", "error": f"Employee '{employee_id}' not found."}

        first_name = employee.get("first_name") or "New"
        last_name = employee.get("last_name") or "Employee"
        department = employee.get("department") or inputs.get("department")
        organization_id = employee.get("organization_id")

        org = await organizations_repo.get(organization_id) if organization_id else None
        org_slug = _slugify((org or {}).get("slug")) or "echo"

        corporate_email = await self._generate_corporate_email(first_name, last_name, org_slug, organization_id)
        employee_number = self._generate_employee_number()
        groups = _groups_for_department(department)

        profile = dict(employee.get("profile") or {})
        profile.update(
            {
                "corporate_email": corporate_email,
                "employee_number": employee_number,
                "groups": groups,
            }
        )
        await employees_repo.update(employee_id, {"profile": profile})

        # Only mint a temporary password when there is no login account yet - an
        # invitation-accepted employee typically already registered one.
        existing_user = await users_repo.get_by_employee_id(employee_id)
        temporary_password = None if existing_user else secrets.token_urlsafe(9)

        user = await AuthService.ensure_user_for_employee(employee, password=temporary_password)

        result: Dict[str, Any] = {
            "status": "success",
            "mode": "live",
            "account_id": user.get("id"),
            "employee_id": employee_id,
            "corporate_email": corporate_email,
            "employee_number": employee_number,
            "groups": groups,
            "details": f"Provisioned corporate identity for {first_name} {last_name} ({corporate_email}).",
        }
        if temporary_password and not existing_user:
            result["temporary_password"] = temporary_password
        return result

    async def _activate(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        from repositories import employees as employees_repo
        from repositories import users as users_repo

        employee_id = inputs["employee_id"]
        now = datetime.utcnow().isoformat()
        await employees_repo.update(employee_id, {"status": "active", "activated_at": now})

        user = await users_repo.get_by_employee_id(employee_id)
        if user:
            await users_repo.update(user["id"], {"is_active": True})

        return {
            "status": "success",
            "mode": "live",
            "employee_id": employee_id,
            "account_status": "active",
            "details": f"Activated employee {employee_id}.",
        }

    async def _deactivate(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        from repositories import employees as employees_repo
        from repositories import users as users_repo

        employee_id = inputs["employee_id"]
        await employees_repo.update(employee_id, {"status": "rejected"})

        user = await users_repo.get_by_employee_id(employee_id)
        if user:
            await users_repo.update(user["id"], {"is_active": False})

        return {
            "status": "success",
            "mode": "live",
            "employee_id": employee_id,
            "account_status": "rejected",
            "details": f"Deactivated employee {employee_id}.",
        }

    async def _assign_groups(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        from repositories import employees as employees_repo

        employee_id = inputs["employee_id"]
        employee = await employees_repo.get(employee_id)
        if not employee:
            return {"status": "failed", "mode": "live", "error": f"Employee '{employee_id}' not found."}

        department = inputs.get("department") or employee.get("department")
        groups = inputs.get("groups") or _groups_for_department(department)

        profile = dict(employee.get("profile") or {})
        profile["groups"] = groups
        await employees_repo.update(employee_id, {"profile": profile})

        return {
            "status": "success",
            "mode": "live",
            "employee_id": employee_id,
            "groups": groups,
            "details": f"Assigned groups {groups} to employee {employee_id}.",
        }

    async def _generate_corporate_email(
        self, first_name: str, last_name: str, org_slug: str, organization_id: Optional[str]
    ) -> str:
        from repositories import employees as employees_repo

        base = f"{_slugify(first_name)}.{_slugify(last_name)}"
        domain = f"{org_slug}.com"
        candidate = f"{base}@{domain}"

        existing_emails: set = set()
        if organization_id:
            try:
                rows = await employees_repo.list_by_organization(organization_id)
                existing_emails = {
                    ((row.get("profile") or {}).get("corporate_email") or "").lower() for row in rows
                }
            except Exception as exc:
                logger.warning("Could not check existing corporate emails for dedup", exc_info=exc)

        if candidate.lower() not in existing_emails:
            return candidate

        suffix = 2
        while f"{base}{suffix}@{domain}".lower() in existing_emails:
            suffix += 1
        return f"{base}{suffix}@{domain}"

    def _generate_employee_number(self) -> str:
        year = datetime.utcnow().year
        return f"EMP-{year}-{secrets.randbelow(10000):04d}"

    async def _audit(self, action: str, inputs: Dict[str, Any], result: Dict[str, Any]) -> None:
        try:
            from services.audit import AuditService

            await AuditService.record(
                action=f"plugin.{self.tool_name}.{action}",
                resource_type="integration",
                resource_id=inputs.get("employee_id", "system"),
                actor=self.tool_name,
                actor_type="agent",
                changes=result,
            )
        except Exception as exc:
            logger.warning("Failed to record audit trail for identity plugin", exc_info=exc)
