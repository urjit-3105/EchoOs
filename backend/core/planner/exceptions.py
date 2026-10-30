class PlanningError(Exception):
    """Base exception for all planning-related errors."""
    pass

class CircularDependencyError(PlanningError):
    """Raised when a circular dependency is detected in the workflow DAG."""
    pass

class MissingDocumentsError(PlanningError):
    """Raised when required documents for the workflow are missing."""
    pass

class MissingApprovalError(PlanningError):
    """Raised when a required approval gate has not been passed."""
    pass

class InvalidWorkflowError(PlanningError):
    """Raised when the workflow definition is invalid."""
    pass

class UnknownTaskError(PlanningError):
    """Raised when a dependency references a non-existent task."""
    pass
