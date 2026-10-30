from typing import Dict, Any
from core.state.models import TaskState
from core.execution.registry import ToolRegistry
from core.logger.structured import get_logger

logger = get_logger(__name__)

class ExecutionPipeline:
    """
    Manages the validation, execution, and rollback of enterprise tool plugins.
    """

    @staticmethod
    async def run(task: TaskState) -> Dict[str, Any]:
        """
        Executes a task through its corresponding tool plugin.
        """
        if not task.tool_name:
            return {"status": "failed", "error": "No tool_name specified in task."}
            
        try:
            plugin = ToolRegistry.get_plugin(task.tool_name)
        except ValueError as e:
            logger.error(f"Plugin {task.tool_name} not found.")
            return {"status": "failed", "error": str(e)}

        # 1. Connect / Health Check
        if not await plugin.health():
            return {"status": "failed", "error": f"Plugin {task.tool_name} is unhealthy."}
            
        await plugin.connect()

        # 2. Validate Inputs
        is_valid = await plugin.validate(task.input_data)
        if not is_valid:
            return {"status": "failed", "error": f"Validation failed for {task.tool_name} inputs."}

        # 3. Execute
        try:
            result = await plugin.execute(task.input_data)
            return result
        except Exception as e:
            logger.error(f"Execution failed for plugin {task.tool_name}.", exc_info=e)
            return {"status": "failed", "error": str(e)}

    @staticmethod
    async def rollback(task: TaskState) -> Dict[str, Any]:
        """
        Attempts to rollback a previously executed task.
        """
        if not task.tool_name:
            return {"status": "failed", "error": "No tool_name specified in task."}
            
        try:
            plugin = ToolRegistry.get_plugin(task.tool_name)
            success = await plugin.rollback(task.output_data or {})
            return {"status": "success" if success else "failed"}
        except Exception as e:
            logger.error(f"Rollback failed for plugin {task.tool_name}.", exc_info=e)
            return {"status": "failed", "error": str(e)}
