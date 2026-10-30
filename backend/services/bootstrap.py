"""Automatic bootstrap service for ECHO WorkforceOS.

Guarantees that on application boot:
1. Default Organization "ECHO WorkforceOS" exists.
2. Enterprise departments ("Executive", "Human Resources", "Administration", "Operations") exist.
3. Four permanent users exist as both Employee records and Authentication accounts:
   - Saatwik (CEO, Executive)
   - Sahithi (Chairman, Executive)
   - Anusha (HR Manager, Human Resources)
   - Sahithy (Clerk, Administration)

This service is 100% idempotent and safe to run repeatedly on application startup.
"""

from typing import Any, Dict, List, Optional

from config.settings import settings
from core.logger.structured import get_logger
from repositories import employees as employees_repo
from repositories import organizations as organizations_repo
from repositories import users as users_repo
from services.auth import AuthService

logger = get_logger(__name__)

DEFAULT_PASSWORD = "EchoDemo123!"

PERMANENT_USERS = [
    {
        "first_name": "Saatwik",
        "last_name": "Pentyala",
        "full_name": "Saatwik Pentyala",
        "email": "admin@echo-workforceos.com",
        "alias_email": "ceo@echo-workforceos.com",
        "role": "admin",
        "job_title": "CEO",
        "department": "Executive",
        "employee_id": "EMP-001",
    },
    {
        "first_name": "Sahithi",
        "last_name": "Pentyala",
        "full_name": "Sahithi Pentyala",
        "email": "sahithi@echo-workforceos.com",
        "role": "admin",
        "job_title": "Chairman",
        "department": "Executive",
        "employee_id": "EMP-002",
    },
    {
        "first_name": "Anusha",
        "last_name": "Pentyala",
        "full_name": "Anusha Pentyala",
        "email": "anusha@echo-workforceos.com",
        "alias_email": "hr@echo-workforceos.com",
        "role": "hr",
        "job_title": "HR Manager",
        "department": "Human Resources",
        "employee_id": "EMP-003",
    },
    {
        "first_name": "Sahithy",
        "last_name": "Pentyala",
        "full_name": "Sahithy Pentyala",
        "email": "sahithy@echo-workforceos.com",
        "role": "employee",
        "job_title": "Clerk",
        "department": "Administration",
        "employee_id": "EMP-004",
    },
]

DEPARTMENTS = ["Executive", "Human Resources", "Administration", "Operations"]


class BootstrapService:
    """Idempotent startup bootstrapper for Organization, Departments, Permanent Users & Auth."""

    @classmethod
    async def initialize(cls) -> Dict[str, Any]:
        """Main startup entry point - called during FastAPI lifespan boot."""
        logger.info("Initializing BootstrapService...")
        org = await cls.seedOrganization()
        await cls.seedDepartments(org["id"])
        await cls.seedUsers(org["id"])
        await cls.ensureAdminAccounts(org["id"])
        logger.info("BootstrapService initialization complete.")
        return org

    @classmethod
    async def seedOrganization(cls) -> Dict[str, Any]:
        """Check whether default organization exists; create if missing."""
        existing = await organizations_repo.get_default()
        if existing:
            return existing

        # Check by name or slug
        all_orgs = await organizations_repo.list()
        for org in all_orgs:
            if org.get("name") == "ECHO WorkforceOS" or org.get("slug") == "echo-workforceos":
                return org

        created = await organizations_repo.create({
            "name": "ECHO WorkforceOS",
            "slug": "echo-workforceos",
            "industry": "Artificial Intelligence & HR Tech",
            "size": "500-1000",
            "settings": {
                "departments": DEPARTMENTS,
                "workflow_auto_start": True,
            }
        })
        logger.info("Seeded default organization: ECHO WorkforceOS", context={"org_id": created["id"]})
        return created

    @classmethod
    async def seedDepartments(cls, organization_id: str) -> List[str]:
        """Ensure enterprise departments hierarchy exists on the organization."""
        org = await organizations_repo.get(organization_id)
        if not org:
            return DEPARTMENTS

        current_settings = dict(org.get("settings") or {})
        current_depts = list(current_settings.get("departments") or [])
        updated_depts = list(set(current_depts + DEPARTMENTS))

        if len(updated_depts) != len(current_depts):
            current_settings["departments"] = updated_depts
            await organizations_repo.update(organization_id, {"settings": current_settings})
            logger.info("Updated organization departments", context={"departments": updated_depts})

        return DEPARTMENTS

    @classmethod
    async def seedUsers(cls, organization_id: str) -> List[Dict[str, Any]]:
        """Create employee records for the 4 permanent users if missing."""
        seeded_employees = []

        for user_def in PERMANENT_USERS:
            emails_to_check = [user_def["email"]]
            if "alias_email" in user_def:
                emails_to_check.append(user_def["alias_email"])

            emp_record = None
            for email in emails_to_check:
                emp_record = await employees_repo.get_by_email(email)
                if emp_record:
                    break

            if not emp_record:
                emp_record = await employees_repo.create({
                    "organization_id": organization_id,
                    "first_name": user_def["first_name"],
                    "last_name": user_def["last_name"],
                    "full_name": user_def["full_name"],
                    "email": user_def["email"],
                    "department": user_def["department"],
                    "job_title": user_def["job_title"],
                    "role": user_def["role"],
                    "status": "active",
                    "profile": {
                        "employee_code": user_def["employee_id"],
                        "job_title": user_def["job_title"],
                        "department": user_def["department"],
                    },
                    "profile_completed": True,
                })
                logger.info(f"Seeded employee record: {user_def['full_name']} ({user_def['email']})")

            # Also check alias email (e.g. ceo@ / hr@) and ensure employee record exists
            if "alias_email" in user_def:
                alias_rec = await employees_repo.get_by_email(user_def["alias_email"])
                if not alias_rec:
                    await employees_repo.create({
                        "organization_id": organization_id,
                        "first_name": user_def["first_name"],
                        "last_name": user_def["last_name"],
                        "full_name": user_def["full_name"],
                        "email": user_def["alias_email"],
                        "department": user_def["department"],
                        "job_title": user_def["job_title"],
                        "role": user_def["role"],
                        "status": "active",
                        "profile_completed": True,
                    })

            seeded_employees.append(emp_record)

        return seeded_employees

    @classmethod
    async def ensureAdminAccounts(cls, organization_id: str) -> List[Dict[str, Any]]:
        """Create authentication accounts with hashed passwords for permanent users."""
        created_accounts = []
        password_hash = AuthService.hash_password(DEFAULT_PASSWORD)

        for user_def in PERMANENT_USERS:
            emails_to_ensure = [user_def["email"]]
            if "alias_email" in user_def:
                emails_to_ensure.append(user_def["alias_email"])

            for email in emails_to_ensure:
                existing_user = await users_repo.get_by_email(email)
                if not existing_user:
                    emp_record = await employees_repo.get_by_email(email)
                    user_account = await users_repo.create({
                        "email": email,
                        "full_name": user_def["full_name"],
                        "password_hash": password_hash,
                        "organization_id": organization_id,
                        "role": user_def["role"],
                        "employee_id": emp_record["id"] if emp_record else None,
                        "is_active": True,
                        "email_verified": True,
                    })
                    logger.info(f"Seeded authentication account: {email}")
                    created_accounts.append(user_account)
                else:
                    created_accounts.append(existing_user)

        return created_accounts
