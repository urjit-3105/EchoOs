from typing import Dict, Any
from core.agents.base import BaseAgent
from core.state.models import ContextState
from core.planner.engine import PlanningEngine
from core.planner.exceptions import PlanningError
from core.orchestrator.registry import AgentRegistry

@AgentRegistry.register("PlannerAgent")
class PlannerAgent(BaseAgent):
    """
    The Planner Agent acts as the brain of the system.
    It does NOT execute tasks or call external tools.
    It analyzes the current workflow state and creates an optimized ExecutionPlan.
    """
    
    def __init__(self):
        super().__init__(name="Planner Agent", capabilities=["planning", "validation", "dependency_resolution"])

    async def validate(self, context: ContextState) -> bool:
        """
        Ensures the Planner Agent has the absolute minimum context required to attempt planning.
        More granular workflow validation happens inside the PlanningEngine.
        """
        if not context.workflow_definition:
            self.logger.error("Missing workflow_definition in context.")
            return False
        return True

    async def execute(self, context: ContextState) -> Dict[str, Any]:
        """
        Invokes the Planning Engine to generate the DAG Execution Plan.
        """
        self.logger.info("Planner Agent starting plan generation...")
        
        try:
            # Generate the execution plan state
            plan_state = PlanningEngine.generate_plan(context, context.workflow_definition)
            
            # Serialize for output
            plan_data = plan_state.model_dump()
            
            self.logger.info("Planning generation successful.", context={"plan_id": plan_state.plan_id})
            
            return {
                "status": "success",
                "plan": plan_data
            }
            
        except PlanningError as pe:
            self.logger.error(f"Planning error occurred: {str(pe)}")
            raise # Let run() catch it and send to recover()

    async def recover(self, context: ContextState, error: Exception) -> Dict[str, Any]:
        """
        Handles planning failures, such as invalid definitions or circular dependencies.
        """
        self.logger.error("Planner Agent failed to generate plan, attempting recovery...", exc_info=error)
        
        # A real implementation might attempt to fetch a fallback template 
        # or immediately escalate to a human ManagerAgent.
        
        return {
            "status": "failed",
            "error_type": type(error).__name__,
            "message": str(error)
        }
