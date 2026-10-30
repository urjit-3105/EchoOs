from typing import Dict, Any, List, Optional
from core.state.models import WorkflowState, ContextState, TaskState
import copy

class WorkflowMemory:
    """
    Manages the runtime memory and context extraction for workflows.
    Ensures that agents only receive the context they need (ContextState).
    """
    
    def __init__(self, initial_state: WorkflowState):
        self._state = initial_state
        self._history: List[Dict[str, Any]] = []

    def get_context_for_task(self, task_id: str) -> ContextState:
        """
        Extracts a localized ContextState for a specific task to pass to an agent.
        """
        if task_id not in self._state.tasks:
            raise ValueError(f"Task {task_id} not found in workflow state.")
            
        task = self._state.tasks[task_id]
        
        # Build dictionary of completed task results
        completed_results = {
            t_id: t.output_data 
            for t_id, t in self._state.tasks.items() 
            if t.status == "completed" and t.output_data
        }
        
        return ContextState(
            workflow_id=self._state.workflow_id,
            employee=self._state.employee,
            current_task=task,
            completed_tasks_results=completed_results,
            global_variables={}, # Could be loaded from config or workflow state
            history=copy.deepcopy(self._history)
        )

    def update_task_result(self, task_id: str, result: Dict[str, Any]):
        """
        Updates the state with the result of a completed task.
        """
        if task_id in self._state.tasks:
            self._state.tasks[task_id].output_data = result
            self._state.tasks[task_id].status = "completed"
            
            # Record in history
            self._history.append({
                "action": "task_completed",
                "task_id": task_id,
                "result": result
            })

    def get_full_state(self) -> WorkflowState:
        """Returns a snapshot of the full workflow state."""
        return copy.deepcopy(self._state)
