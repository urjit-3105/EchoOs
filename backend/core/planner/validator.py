from typing import Dict, Any, List
from core.state.models import ContextState
from core.planner.exceptions import InvalidWorkflowError, MissingDocumentsError, MissingApprovalError

class WorkflowValidator:
    """Validates the workflow definition and context state before planning."""

    @staticmethod
    def validate(context: ContextState, definition: Dict[str, Any]) -> bool:
        """
        Runs all validation checks on the workflow.
        Returns True if valid, raises PlanningError exceptions otherwise.
        """
        WorkflowValidator._validate_definition(definition)
        WorkflowValidator._validate_documents(context, definition)
        WorkflowValidator._validate_approvals(context, definition)
        return True

    @staticmethod
    def _validate_definition(definition: Dict[str, Any]):
        if not definition:
            raise InvalidWorkflowError("Workflow definition is empty.")
        if "id" not in definition or "tasks" not in definition:
            raise InvalidWorkflowError("Workflow definition must contain 'id' and 'tasks'.")
        
        # Check that tasks is a list
        if not isinstance(definition["tasks"], list):
            raise InvalidWorkflowError("'tasks' must be a list of task definitions.")

    @staticmethod
    def _validate_documents(context: ContextState, definition: Dict[str, Any]):
        # Example validation: if workflow requires specific documents
        required_docs = definition.get("required_documents", [])
        # Assume context.global_variables might store uploaded doc IDs for now
        # or we might fetch this from a service in a real scenario
        # This is a basic stub
        if required_docs and not context.global_variables.get("documents"):
             # If required, and no documents provided
             pass # In real scenario, we'd check actual existence

    @staticmethod
    def _validate_approvals(context: ContextState, definition: Dict[str, Any]):
        # If the workflow requires a prior approval to even generate a plan
        if definition.get("requires_initial_approval"):
            if not context.global_variables.get("initial_approval_granted"):
                raise MissingApprovalError("Initial manager approval is missing for this workflow.")
