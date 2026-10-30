from core.state.models import ContextState, VerificationReportState, VerificationOutcome
from core.verification.validators.profile import ProfileValidator
from core.verification.validators.document import DocumentValidator
from core.verification.validators.policy import PolicyValidator
from core.logger.structured import get_logger

logger = get_logger(__name__)

class DecisionEngine:
    """
    Executes all validators and synthesizes the VerificationReport.
    """

    @staticmethod
    def evaluate(context: ContextState) -> VerificationReportState:
        logger.info(f"Starting verification for workflow {context.workflow_id}")
        
        report = VerificationReportState()
        
        # 1. Profile Validation
        profile_res = ProfileValidator.validate(context)
        if not profile_res["is_valid"]:
            report.required_corrections.extend([f"Missing profile field: {f}" for f in profile_res["missing_fields"]])
            
        # 2. Document Validation
        doc_res = DocumentValidator.validate(context)
        report.missing_documents.extend(doc_res["missing_docs"])
        report.invalid_documents.extend(doc_res["invalid_docs"])
        
        # 3. Policy/Compliance Validation
        policy_res = PolicyValidator.validate(context)
        report.compliance_findings.extend(policy_res["findings"])
        
        # 4. Final Decision Synthesis
        if not profile_res["is_valid"] or len(doc_res["missing_docs"]) > 0:
            report.overall_status = VerificationOutcome.INFO_REQUIRED
            report.confidence_score = 0.0
            report.next_action = "REQUEST_DOCUMENTS"
            report.warnings.append("Critical requirements are missing. Blocking workflow.")
        elif len(doc_res["invalid_docs"]) > 0 or len(policy_res["findings"]) > 0:
            report.overall_status = VerificationOutcome.HUMAN_REVIEW
            report.confidence_score = 0.5
            report.next_action = "ESCALATE_TO_MANAGER"
            report.warnings.append("Documents are expired or policies violated. Human review required.")
        else:
            report.overall_status = VerificationOutcome.PASSED
            report.confidence_score = 1.0
            report.next_action = "PROCEED"
            report.recommendations.append("All checks passed.")
            
        logger.info(f"Verification finished with status {report.overall_status}", context={"workflow_id": context.workflow_id})
        
        return report
