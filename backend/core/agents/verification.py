from typing import Dict, Any
from core.agents.base import BaseAgent
from core.state.models import ContextState, VerificationOutcome
from core.verification.engine import DecisionEngine
from core.orchestrator.events import OrchestratorEventDispatcher
from core.orchestrator.registry import AgentRegistry

@AgentRegistry.register("VerificationAgent")
class VerificationAgent(BaseAgent):
    """
    Autonomous Verification & Compliance Agent.
    Evaluates employee context against configurable rules and returns a structured VerificationReport.
    """
    def __init__(self):
        super().__init__(name="Verification Agent", capabilities=["document_verification", "compliance_checks", "policy_validation"])

    async def validate(self, context: ContextState) -> bool:
        # Pre-flight check before execution
        if not context.employee:
            return False
        return True

    async def execute(self, context: ContextState) -> Dict[str, Any]:
        self.logger.info("Verification Agent evaluating context...", context={"workflow_id": context.workflow_id})
        
        await OrchestratorEventDispatcher.dispatch("VerificationAgent.Started", context.workflow_id)

        # Execute decision engine
        report = DecisionEngine.evaluate(context)
        
        # Publish granular events based on outcome
        if report.overall_status == VerificationOutcome.PASSED:
            await OrchestratorEventDispatcher.dispatch("VerificationAgent.Passed", context.workflow_id)
        elif report.overall_status == VerificationOutcome.INFO_REQUIRED:
            await OrchestratorEventDispatcher.dispatch("VerificationAgent.MissingDocuments", context.workflow_id, {"missing": report.missing_documents})
        elif report.overall_status == VerificationOutcome.HUMAN_REVIEW:
            await OrchestratorEventDispatcher.dispatch("VerificationAgent.HumanReviewRequired", context.workflow_id, {"findings": report.compliance_findings})
        elif report.overall_status == VerificationOutcome.FAILED:
            await OrchestratorEventDispatcher.dispatch("VerificationAgent.Failed", context.workflow_id)
            
        return {
            "status": "success",
            "report": report.model_dump()
        }

    async def recover(self, context: ContextState, error: Exception) -> Dict[str, Any]:
        self.logger.error("Verification Agent encountered critical fault.", exc_info=error)
        return {"status": "failed", "error": str(error)}
