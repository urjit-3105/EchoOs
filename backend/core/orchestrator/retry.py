import asyncio
from typing import Dict, Any
from core.state.models import TaskPlanState, TaskStatus
from core.logger.structured import get_logger
from core.orchestrator.events import OrchestratorEventDispatcher, OrchestratorEvents

logger = get_logger(__name__)

class RetryManager:
    """
    Handles task failures, exponential backoffs, and escalation routing.
    """
    
    @staticmethod
    async def handle_failure(workflow_id: str, task: TaskPlanState, error_msg: str) -> str:
        """
        Evaluates a task failure against its RetryPolicy.
        Returns the action to take: "retry" or "escalate"
        """
        policy = task.retry_policy
        policy.attempts += 1
        policy.last_error = error_msg
        
        logger.warning(
            f"Task {task.task_id} failed (Attempt {policy.attempts}/{policy.max_retries}).",
            context={"workflow_id": workflow_id, "error": error_msg}
        )
        
        if policy.attempts < policy.max_retries:
            # Calculate exponential backoff (e.g., base delay * 2^attempts)
            # In a true distributed system, we'd schedule this in a delayed message queue (e.g. Celery).
            # For this MVP runtime, we'll return "retry" and let the runtime handle the delay if necessary.
            
            await OrchestratorEventDispatcher.dispatch(
                OrchestratorEvents.TASK_RETRIED, 
                workflow_id, 
                {"task_id": task.task_id, "attempt": policy.attempts}
            )
            return "retry"
        else:
            logger.error(
                f"Task {task.task_id} exhausted all retries. Escalating.",
                context={"workflow_id": workflow_id}
            )
            return "escalate"
