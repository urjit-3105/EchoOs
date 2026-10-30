from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class WorkflowStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"

class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class VerificationOutcome(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    PENDING = "pending"
    HUMAN_REVIEW = "human_review"
    INFO_REQUIRED = "info_required"

class EmployeeState(BaseModel):
    id: str
    first_name: str
    last_name: str
    email: str
    department: Optional[str] = None
    role: Optional[str] = None
    onboarding_date: Optional[datetime] = None

class RetryState(BaseModel):
    attempts: int = 0
    max_retries: int = Field(default=3, description="Maximum number of retry attempts")
    last_error: Optional[str] = None
    next_retry_at: Optional[datetime] = None

class ApprovalState(BaseModel):
    required: bool = False
    status: ApprovalStatus = ApprovalStatus.PENDING
    approver_id: Optional[str] = None
    approved_at: Optional[datetime] = None
    comments: Optional[str] = None

class TaskState(BaseModel):
    task_id: str
    name: str
    assigned_agent: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    tool_name: Optional[str] = None
    input_data: Dict[str, Any] = Field(default_factory=dict)
    output_data: Optional[Dict[str, Any]] = None
    retry_state: RetryState = Field(default_factory=RetryState)
    approval_state: ApprovalState = Field(default_factory=ApprovalState)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class ExecutionState(BaseModel):
    current_task_id: Optional[str] = None
    completed_tasks: List[str] = Field(default_factory=list)
    failed_tasks: List[str] = Field(default_factory=list)
    active_branches: int = 1
    total_execution_time_seconds: float = 0.0

class WorkflowState(BaseModel):
    workflow_id: str
    name: str
    status: WorkflowStatus = WorkflowStatus.PENDING
    employee: EmployeeState
    tasks: Dict[str, TaskState] = Field(default_factory=dict)
    execution: ExecutionState = Field(default_factory=ExecutionState)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class DocumentState(BaseModel):
    id: str
    type: str
    upload_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    required: bool = False
    verification_status: str = "pending"
    validation_errors: List[str] = Field(default_factory=list)

class VerificationReportState(BaseModel):
    overall_status: VerificationOutcome = VerificationOutcome.PENDING
    confidence_score: float = 0.0
    missing_documents: List[str] = Field(default_factory=list)
    invalid_documents: List[str] = Field(default_factory=list)
    required_corrections: List[str] = Field(default_factory=list)
    compliance_findings: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    next_action: str = "WAIT"

class ContextState(BaseModel):
    """
    The unified context passed to AI Agents containing everything they need to execute.
    """
    workflow_id: str
    employee: EmployeeState
    current_task: TaskState
    completed_tasks_results: Dict[str, Any] = Field(default_factory=dict)
    global_variables: Dict[str, Any] = Field(default_factory=dict)
    history: List[Dict[str, Any]] = Field(default_factory=list)
    configuration: Dict[str, Any] = Field(default_factory=dict)
    workflow_definition: Dict[str, Any] = Field(default_factory=dict)

class TaskPlanState(BaseModel):
    task_id: str
    name: str
    description: Optional[str] = None
    assigned_agent: Optional[str] = None
    tool_name: Optional[str] = None
    priority: int = 0
    dependencies: List[str] = Field(default_factory=list)
    estimated_duration_seconds: int = 0
    retry_policy: RetryState = Field(default_factory=RetryState)
    required_inputs: List[str] = Field(default_factory=list)
    expected_outputs: List[str] = Field(default_factory=list)
    status: str = "pending" # pending, scheduled, active
    stage: Optional[str] = None
    requires_approval: bool = False
    approval_condition: str = "always"  # always | verification_not_passed | never
    approval_role: str = "hr"
    on_failure: str = "retry"  # retry | escalate | skip | fail_workflow
    input_data: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    output_data: Optional[Dict[str, Any]] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class ExecutionPlanState(BaseModel):
    plan_id: str
    workflow_id: str
    tasks: Dict[str, TaskPlanState] = Field(default_factory=dict)
    critical_path: List[str] = Field(default_factory=list)
    estimated_total_duration: int = 0
    status: str = "generated"
    template_key: Optional[str] = None
    stages: List[Dict[str, Any]] = Field(default_factory=list)
