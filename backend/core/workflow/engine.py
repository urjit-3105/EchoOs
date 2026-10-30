from typing import Dict, Any, List
import yaml
import json
import asyncio
from core.state.models import WorkflowState, TaskState, WorkflowStatus, TaskStatus
from core.state.memory import WorkflowMemory
from core.logger.structured import get_logger
from core.events.bus import EventBus, EventType
from config.settings import settings

logger = get_logger(__name__)

class WorkflowEngine:
    """
    DEPRECATED: This basic DAG engine from Phase 2 has been superseded by the 
    Multi-Agent Orchestrator (core/orchestrator/).
    Please use core.orchestrator.service.OrchestratorService instead.
    """
    
    def __init__(self):
        self.workflows: Dict[str, dict] = {}
        
    def load_from_yaml(self, file_path: str):
        """Loads a workflow definition from a YAML file."""
        try:
            with open(file_path, 'r') as f:
                definition = yaml.safe_load(f)
                self.workflows[definition['id']] = definition
                logger.info(f"Loaded workflow definition: {definition['id']}")
        except Exception as e:
            logger.error(f"Failed to load workflow from {file_path}", exc_info=e)

    def load_from_json(self, json_str: str):
        """Loads a workflow definition from a JSON string."""
        try:
            definition = json.loads(json_str)
            self.workflows[definition['id']] = definition
            logger.info(f"Loaded workflow definition: {definition['id']}")
        except Exception as e:
            logger.error("Failed to load workflow from JSON", exc_info=e)

    async def execute_workflow(self, state: WorkflowState) -> WorkflowState:
        """
        Executes a workflow state using the loaded definition.
        Handles dependencies and parallel execution.
        """
        if state.name not in self.workflows:
            raise ValueError(f"Workflow definition '{state.name}' not found.")
            
        definition = self.workflows[state.name]
        memory = WorkflowMemory(state)
        
        state.status = WorkflowStatus.RUNNING
        logger.info(f"Starting execution of workflow {state.workflow_id}")
        
        try:
            # Simple DAG Execution logic (Breadth-First)
            # In a real enterprise system, this would use a robust graph traversal algorithm.
            
            # Step 1: Initialize tasks from definition if they don't exist
            if not state.tasks:
                for task_def in definition.get('tasks', []):
                    task = TaskState(
                        task_id=task_def['id'],
                        name=task_def['name'],
                        assigned_agent=task_def.get('agent')
                    )
                    state.tasks[task.task_id] = task
            
            # Step 2: Execution loop
            while self._has_pending_tasks(state):
                executable_tasks = self._get_executable_tasks(state, definition)
                
                if not executable_tasks:
                    # Deadlock detected or waiting on external approval
                    logger.warning(f"Workflow {state.workflow_id} stalled. No executable tasks.")
                    break
                    
                # Execute in parallel
                execution_coroutines = [
                    self._execute_task(task_id, memory) for task_id in executable_tasks
                ]
                
                results = await asyncio.gather(*execution_coroutines, return_exceptions=True)
                
                for task_id, result in zip(executable_tasks, results):
                    if isinstance(result, Exception):
                        logger.error(f"Task {task_id} failed fatally.", exc_info=result)
                        state.tasks[task_id].status = TaskStatus.FAILED
                    
            # Check overall status
            if any(t.status == TaskStatus.FAILED for t in state.tasks.values()):
                state.status = WorkflowStatus.FAILED
                await EventBus.publish(EventType.WorkflowFailed, {"workflow_id": state.workflow_id})
            else:
                state.status = WorkflowStatus.COMPLETED
                await EventBus.publish(EventType.WorkflowCompleted, {"workflow_id": state.workflow_id})
                
            return memory.get_full_state()
            
        except Exception as e:
            logger.error(f"Workflow {state.workflow_id} failed abruptly.", exc_info=e)
            state.status = WorkflowStatus.FAILED
            await EventBus.publish(EventType.WorkflowFailed, {"workflow_id": state.workflow_id})
            return state

    def _has_pending_tasks(self, state: WorkflowState) -> bool:
        return any(t.status in (TaskStatus.PENDING, TaskStatus.IN_PROGRESS) for t in state.tasks.values())

    def _get_executable_tasks(self, state: WorkflowState, definition: dict) -> List[str]:
        executable = []
        for task_def in definition.get('tasks', []):
            task_id = task_def['id']
            task = state.tasks.get(task_id)
            
            if not task or task.status != TaskStatus.PENDING:
                continue
                
            # Check dependencies
            deps = task_def.get('depends_on', [])
            can_execute = True
            for dep in deps:
                dep_task = state.tasks.get(dep)
                if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                    can_execute = False
                    break
                    
            if can_execute:
                executable.append(task_id)
                
        return executable

    async def _execute_task(self, task_id: str, memory: WorkflowMemory):
        """
        Executes a single task by invoking the assigned agent.
        """
        state = memory.get_full_state()
        task = state.tasks[task_id]
        
        task.status = TaskStatus.IN_PROGRESS
        logger.info(f"Executing task: {task_id}")
        
        # In a real implementation, this would instantiate the specific agent
        # via an AgentRegistry or Factory and call agent.run(context)
        
        # Simulating execution latency
        await asyncio.sleep(0.5)
        
        # Simulated success
        result = {"status": "success", "data": f"Executed {task.name}"}
        
        memory.update_task_result(task_id, result)
        logger.info(f"Task {task_id} completed successfully.")
        return result
