import unittest
from datetime import datetime, timedelta, timezone
from core.state.models import ContextState, EmployeeState, TaskState, DocumentState, VerificationOutcome
from core.verification.engine import DecisionEngine
from core.verification.rules import RuleEngine

class TestVerificationAgent(unittest.TestCase):
    def setUp(self):
        RuleEngine.load_rules()
        self.employee = EmployeeState(
            id="emp-1",
            first_name="Jane",
            last_name="Doe",
            email="jane@example.com",
            department="Engineering",
            role="Developer"
        )
        self.context = ContextState(
            workflow_id="wf-test",
            employee=self.employee,
            current_task=TaskState(task_id="mock", name="mock")
        )

    def test_missing_profile_fields(self):
        # Missing last_name and email
        bad_employee = EmployeeState(
            id="emp-2",
            first_name="John",
            last_name="", # Empty string, basically falsy
            email=""
        )
        self.context.employee = bad_employee
        
        report = DecisionEngine.evaluate(self.context)
        
        self.assertEqual(report.overall_status, VerificationOutcome.INFO_REQUIRED)
        self.assertTrue(any("last_name" in c for c in report.required_corrections))
        self.assertTrue(any("email" in c for c in report.required_corrections))

    def test_missing_documents(self):
        # Provide only Offer Letter, missing I-9 and Engineering specific docs
        self.context.global_variables["documents"] = [
            DocumentState(id="d1", type="Offer Letter").model_dump()
        ]
        
        report = DecisionEngine.evaluate(self.context)
        
        self.assertEqual(report.overall_status, VerificationOutcome.INFO_REQUIRED)
        self.assertIn("I-9 Form", report.missing_documents)
        self.assertIn("Non-Disclosure Agreement (NDA)", report.missing_documents)

    def test_expired_documents(self):
        expired_date = datetime.now(timezone.utc) - timedelta(days=5)
        self.context.global_variables["documents"] = [
            DocumentState(id="d1", type="Offer Letter").model_dump(),
            DocumentState(id="d2", type="I-9 Form", expiry_date=expired_date).model_dump(),
            DocumentState(id="d3", type="Non-Disclosure Agreement (NDA)").model_dump(),
            DocumentState(id="d4", type="Invention Assignment Agreement").model_dump()
        ]
        
        report = DecisionEngine.evaluate(self.context)
        
        # We provided all docs, so nothing missing, but I-9 is expired
        self.assertEqual(report.overall_status, VerificationOutcome.HUMAN_REVIEW)
        self.assertIn("I-9 Form is expired", report.invalid_documents)

    def test_policy_violation(self):
        # Role requires background check
        self.context.employee.role = "Manager"
        
        # Provide all required documents (Global + Engineering)
        self.context.global_variables["documents"] = [
            DocumentState(id="d1", type="Offer Letter").model_dump(),
            DocumentState(id="d2", type="I-9 Form").model_dump(),
            DocumentState(id="d3", type="Non-Disclosure Agreement (NDA)").model_dump(),
            DocumentState(id="d4", type="Invention Assignment Agreement").model_dump()
        ]
        
        # Missing background check
        report = DecisionEngine.evaluate(self.context)
        self.assertEqual(report.overall_status, VerificationOutcome.HUMAN_REVIEW)
        self.assertTrue(any("Background check is required" in f for f in report.compliance_findings))

    def test_passed_verification(self):
        self.context.global_variables["documents"] = [
            DocumentState(id="d1", type="Offer Letter").model_dump(),
            DocumentState(id="d2", type="I-9 Form").model_dump(),
            DocumentState(id="d3", type="Non-Disclosure Agreement (NDA)").model_dump(),
            DocumentState(id="d4", type="Invention Assignment Agreement").model_dump()
        ]
        
        report = DecisionEngine.evaluate(self.context)
        self.assertEqual(report.overall_status, VerificationOutcome.PASSED)
        self.assertEqual(report.confidence_score, 1.0)
        self.assertEqual(len(report.missing_documents), 0)

if __name__ == "__main__":
    unittest.main()
