from typing import Dict, Any
from core.events.bus import EventBus
from core.logger.structured import get_logger

logger = get_logger(__name__)

class OrchestratorEventDispatcher:
    """
    Standardized event dispatcher for the Multi-Agent Orchestrator.
    Wraps the underlying EventBus.
    """
    
    @staticmethod
    async def dispatch(event_type: str, workflow_id: str, payload: Dict[str, Any] = None):
        """
        Dispatches an event with standardized workflow tracing metadata.
        """
        full_payload = {
            "workflow_id": workflow_id,
            **(payload or {})
        }
        logger.info(f"Orchestrator dispatching event: {event_type}", context=full_payload)
        await EventBus.publish(event_type, full_payload)

# Predefined Orchestrator Events
class OrchestratorEvents:
    WORKFLOW_STARTED = "Orchestrator.WorkflowStarted"
    WORKFLOW_PAUSED = "Orchestrator.WorkflowPaused"
    WORKFLOW_COMPLETED = "Orchestrator.WorkflowCompleted"
    WORKFLOW_FAILED = "Orchestrator.WorkflowFailed"
    WORKFLOW_CANCELLED = "Orchestrator.WorkflowCancelled"
    
    TASK_READY = "Orchestrator.TaskReady"
    TASK_STARTED = "Orchestrator.TaskStarted"
    TASK_COMPLETED = "Orchestrator.TaskCompleted"
    TASK_FAILED = "Orchestrator.TaskFailed"
    TASK_RETRIED = "Orchestrator.TaskRetried"
    
    APPROVAL_REQUESTED = "Orchestrator.ApprovalRequested"
    APPROVAL_GRANTED = "Orchestrator.ApprovalGranted"
    APPROVAL_REJECTED = "Orchestrator.ApprovalRejected"
    
    VERIFICATION_STARTED = "VerificationAgent.Started"
    VERIFICATION_PASSED = "VerificationAgent.Passed"
    VERIFICATION_FAILED = "VerificationAgent.Failed"
    VERIFICATION_MISSING_DOCS = "VerificationAgent.MissingDocuments"
    VERIFICATION_HUMAN_REVIEW = "VerificationAgent.HumanReviewRequired"
    
    EXECUTION_STARTED = "ExecutionAgent.TaskExecutionStarted"
    EXECUTION_COMPLETED = "ExecutionAgent.TaskExecutionCompleted"
    EXECUTION_FAILED = "ExecutionAgent.TaskExecutionFailed"
    EXECUTION_ROLLBACK_STARTED = "ExecutionAgent.RollbackStarted"
    EXECUTION_ROLLBACK_COMPLETED = "ExecutionAgent.RollbackCompleted"
