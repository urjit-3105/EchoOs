from core.state.models import TaskPlanState
from core.logger.structured import get_logger
from core.orchestrator.events import OrchestratorEventDispatcher, OrchestratorEvents

logger = get_logger(__name__)

class ApprovalManager:
    """
    Manages workflow pauses and resumes for human-in-the-loop checkpoints.
    """

    @staticmethod
    async def request_approval(workflow_id: str, task: TaskPlanState) -> None:
        """
        Pauses the task execution and emits an approval request event.
        """
        logger.info(f"Task {task.task_id} requires human approval.", context={"workflow_id": workflow_id})
        
        await OrchestratorEventDispatcher.dispatch(
            OrchestratorEvents.APPROVAL_REQUESTED,
            workflow_id,
            {"task_id": task.task_id}
        )

    @staticmethod
    async def process_approval(workflow_id: str, task: TaskPlanState, approved: bool, reviewer: str = None) -> bool:
        """
        Processes an incoming approval or rejection.
        """
        if approved:
            logger.info(f"Task {task.task_id} approved by {reviewer}.", context={"workflow_id": workflow_id})
            await OrchestratorEventDispatcher.dispatch(
                OrchestratorEvents.APPROVAL_GRANTED,
                workflow_id,
                {"task_id": task.task_id, "reviewer": reviewer}
            )
            return True
        else:
            logger.warning(f"Task {task.task_id} rejected by {reviewer}.", context={"workflow_id": workflow_id})
            await OrchestratorEventDispatcher.dispatch(
                OrchestratorEvents.APPROVAL_REJECTED,
                workflow_id,
                {"task_id": task.task_id, "reviewer": reviewer}
            )
            return False
