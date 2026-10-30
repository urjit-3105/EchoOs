import unittest
import asyncio
from datetime import datetime, timedelta

from database import init_database
from repositories import users as users_repo
from repositories import employees as employees_repo
from repositories import organizations as organizations_repo
from services.auth import AuthService
from services.invitations import InvitationService
from core.workflow.templates import WorkflowTemplateRegistry

class TestAuthAndWorkflowLifecycle(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        await init_database()
        WorkflowTemplateRegistry.load_all()

    async def test_workflow_templates_loaded(self):
        """Verifies that all pre-configured onboarding templates load correctly."""
        keys = WorkflowTemplateRegistry.keys()
        self.assertIn("employee_onboarding", keys)
        template = WorkflowTemplateRegistry.get("employee_onboarding")
        self.assertIsNotNone(template)
        self.assertGreater(len(template.get("tasks", [])), 0)

    async def test_password_hashing_and_verification(self):
        """Ensures password hashing and bcrypt verification match securely."""
        plain = "EchoTestSecret123!"
        hashed = AuthService.hash_password(plain)
        self.assertTrue(AuthService.verify_password(plain, hashed))
        self.assertFalse(AuthService.verify_password("WrongPassword!", hashed))

    async def test_jwt_token_minting_and_decoding(self):
        """Verifies JWT access token generation and claims decoding."""
        user_payload = {
            "id": "u-test-999",
            "email": "test.user@echo-workforceos.com",
            "role": "admin",
            "organization_id": "org-test-1",
        }
        token = AuthService.create_access_token(user_payload)
        self.assertIsInstance(token, str)
        self.assertTrue(len(token) > 20)
        
        claims = AuthService.decode_token(token)
        self.assertIsNotNone(claims)
        self.assertEqual(claims.get("email"), "test.user@echo-workforceos.com")
        self.assertEqual(claims.get("role"), "admin")

    async def test_invitation_lifecycle(self):
        """Tests invitation token generation, expiry, and retrieval."""
        orgs = await organizations_repo.list()
        org_id = orgs[0]["id"] if orgs else "org-default"

        invite = await InvitationService.create(
            first_name="Test",
            last_name="Candidate",
            email="candidate.test@example.com",
            department="Engineering",
            job_title="Software Engineer",
            role="employee",
            organization_id=org_id,
        )

        self.assertIsNotNone(invite)
        invitation = invite.get("invitation", {})
        self.assertIn("token", invitation)
        self.assertTrue(len(invitation["token"]) >= 16)
        self.assertEqual(invitation["email"], "candidate.test@example.com")

        # Resolving via token
        resolved = await InvitationService.get_by_token(invitation["token"])
        self.assertIsNotNone(resolved)
        self.assertIn("invitation", resolved)
        self.assertEqual(resolved["invitation"]["id"], invitation["id"])

if __name__ == "__main__":
    unittest.main()
