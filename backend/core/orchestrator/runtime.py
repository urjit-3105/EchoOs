import asyncio
from core.state.models import ExecutionPlanState, ContextState
from core.orchestrator.execution import ExecutionManager
from core.orchestrator.events import OrchestratorEventDispatcher, OrchestratorEvents
from core.logger.structured import get_logger

logger = get_logger(__name__)

class WorkflowRuntime:
    """
    The main execution loop for a workflow. It consumes an ExecutionPlanState,
    dispatches ready tasks, and continues until completion or failure.
    """

    @staticmethod
    async def run(workflow_id: str, plan: ExecutionPlanState, context: ContextState) -> ExecutionPlanState:
        """
        Starts or resumes the execution loop.
        """
        logger.info(f"Starting WorkflowRuntime for workflow {workflow_id}")
        
        if plan.status == "generated":
            plan.status = "running"
            await OrchestratorEventDispatcher.dispatch(OrchestratorEvents.WORKFLOW_STARTED, workflow_id)

        while True:
            # 0. Stop cleanly if the plan was paused or cancelled out from under us
            # (e.g. a human gate opened mid-batch, or an operator cancelled the run).
            if plan.status in ("paused", "cancelled"):
                logger.info(f"Workflow {workflow_id} loop stopping cleanly (status={plan.status}).")
                break

            # 1. Evaluate State
            ready_tasks = await ExecutionManager.get_ready_tasks(plan)

            # 2. Check for completion or failure
            if not ready_tasks:
                if WorkflowRuntime._is_completed(plan):
                    plan.status = "completed"
                    await OrchestratorEventDispatcher.dispatch(OrchestratorEvents.WORKFLOW_COMPLETED, workflow_id)
                    logger.info(f"Workflow {workflow_id} completed successfully.")
                    break
                elif WorkflowRuntime._has_failed_tasks(plan):
                    plan.status = "failed"
                    await OrchestratorEventDispatcher.dispatch(OrchestratorEvents.WORKFLOW_FAILED, workflow_id)
                    logger.error(f"Workflow {workflow_id} failed due to unrecoverable tasks.")
                    break
                else:
                    # Workflow is paused waiting for external events (e.g., approvals)
                    logger.info(f"Workflow {workflow_id} is blocked or paused.")
                    break

            # 3. Dispatch Batch
            await ExecutionManager.execute_batch(workflow_id, ready_tasks, context, plan)

            # A task in the batch may have paused/cancelled/failed the plan - stop now
            # rather than spinning one more time with nothing left to legally run.
            if plan.status in ("paused", "cancelled", "failed"):
                break

            # Slight delay to prevent aggressive spinning in tight loops
            await asyncio.sleep(0.1)

        return plan

    @staticmethod
    def _is_completed(plan: ExecutionPlanState) -> bool:
        # A skipped task is a resolved branch (on_failure: skip), not an outstanding one.
        return all(task.status in ("completed", "skipped") for task in plan.tasks.values())

    @staticmethod
    def _has_failed_tasks(plan: ExecutionPlanState) -> bool:
        return any(task.status == "failed" for task in plan.tasks.values())
