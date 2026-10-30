from typing import Dict, Any
import time
from core.agents.base import BaseAgent
from core.state.models import ContextState
from core.execution.engine import ExecutionPipeline
from core.orchestrator.events import OrchestratorEventDispatcher
from core.orchestrator.registry import AgentRegistry

@AgentRegistry.register("ExecutionAgent")
class ExecutionAgent(BaseAgent):
    """
    Autonomous Execution Agent.
    Executes tasks using the plugin-based ExecutionPipeline.
    """
    def __init__(self):
        super().__init__(name="Execution Agent", capabilities=["tool_execution", "api_calls", "enterprise_plugins"])

    async def validate(self, context: ContextState) -> bool:
        if not context.current_task or not context.current_task.tool_name:
            self.logger.error("ExecutionAgent received task without a tool_name.")
            return False
        return True

    async def execute(self, context: ContextState) -> Dict[str, Any]:
        task = context.current_task
        workflow_id = context.workflow_id
        
        self.logger.info(f"Execution Agent starting task '{task.task_id}' using tool '{task.tool_name}'", context={"workflow_id": workflow_id})
        await OrchestratorEventDispatcher.dispatch("ExecutionAgent.TaskExecutionStarted", workflow_id, {"task_id": task.task_id, "tool": task.tool_name})
        
        start_time = time.time()
        
        result = await ExecutionPipeline.run(task)
        
        duration = time.time() - start_time
        
        if result.get("status") == "success":
            await OrchestratorEventDispatcher.dispatch("ExecutionAgent.TaskExecutionCompleted", workflow_id, {"task_id": task.task_id, "duration": duration})
            return result
        else:
            await OrchestratorEventDispatcher.dispatch("ExecutionAgent.TaskExecutionFailed", workflow_id, {"task_id": task.task_id, "error": result.get("error")})
            return result

    async def recover(self, context: ContextState, error: Exception) -> Dict[str, Any]:
        task = context.current_task
        workflow_id = context.workflow_id
        
        self.logger.warning(f"Execution Agent fault on task '{task.task_id}'. Attempting rollback.", context={"workflow_id": workflow_id})
        await OrchestratorEventDispatcher.dispatch("ExecutionAgent.RollbackStarted", workflow_id, {"task_id": task.task_id})
        
        rollback_res = await ExecutionPipeline.rollback(task)
        
        if rollback_res.get("status") == "success":
            await OrchestratorEventDispatcher.dispatch("ExecutionAgent.RollbackCompleted", workflow_id, {"task_id": task.task_id})
            
        return {"status": "failed", "error": str(error), "rollback": rollback_res.get("status")}
