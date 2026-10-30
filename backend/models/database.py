import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def _uuid() -> str:
    return str(uuid.uuid4())


# ----------------------------------------------------------------------
# Enums
# ----------------------------------------------------------------------
class WorkflowStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class EmployeeStatus(str, enum.Enum):
    INVITED = "invited"
    ACCEPTED = "accepted"
    PROFILE_PENDING = "profile_pending"
    DOCUMENTS_PENDING = "documents_pending"
    VERIFYING = "verifying"
    AWAITING_APPROVAL = "awaiting_approval"
    PROVISIONING = "provisioning"
    ACTIVE = "active"
    REJECTED = "rejected"


class InvitationStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    EXPIRED = "expired"
    REVOKED = "revoked"


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    HR = "hr"
    MANAGER = "manager"
    EMPLOYEE = "employee"


class ApprovalStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"
    EXPIRED = "expired"


class DocumentStatus(str, enum.Enum):
    PENDING = "pending"
    UPLOADED = "uploaded"
    VERIFIED = "verified"
    REJECTED = "rejected"
    EXPIRED = "expired"


# ----------------------------------------------------------------------
# Tenancy & identity
# ----------------------------------------------------------------------
class Organization(Base):
    __tablename__ = "organizations"

    id = Column(String, primary_key=True, index=True, default=_uuid)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, index=True, nullable=False)
    industry = Column(String)
    size = Column(String)
    logo_url = Column(String)
    timezone = Column(String, default="UTC")
    settings = Column(JSON, default=dict)
    policies = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    users = relationship("User", back_populates="organization")
    employees = relationship("Employee", back_populates="organization")


class User(Base):
    """Authenticated principal. Mirrors a Supabase auth user when Supabase Auth is active."""

    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True, default=_uuid)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String)
    password_hash = Column(String, nullable=True)  # null when Supabase Auth owns the credential
    supabase_user_id = Column(String, nullable=True, index=True)
    role = Column(String, default=UserRole.EMPLOYEE.value, nullable=False)
    employee_id = Column(String, nullable=True, index=True)
    is_active = Column(Boolean, default=True)
    email_verified = Column(Boolean, default=False)
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    organization = relationship("Organization", back_populates="users")


# ----------------------------------------------------------------------
# Workforce
# ----------------------------------------------------------------------
class Employee(Base):
    __tablename__ = "employees"

    id = Column(String, primary_key=True, index=True, default=_uuid)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String)
    department = Column(String)
    role = Column(String)
    job_title = Column(String)
    employment_type = Column(String, default="full_time")
    manager_id = Column(String, nullable=True)
    status = Column(String, default=EmployeeStatus.INVITED.value, index=True)
    onboarding_date = Column(DateTime)
    start_date = Column(DateTime)
    profile = Column(JSON, default=dict)
    profile_completed = Column(Boolean, default=False)
    terms_accepted_at = Column(DateTime, nullable=True)
    policies_reviewed_at = Column(DateTime, nullable=True)
    activated_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    organization = relationship("Organization", back_populates="employees")
    workflows = relationship("Workflow", back_populates="employee")
    documents = relationship("Document", back_populates="employee")


class Invitation(Base):
    __tablename__ = "invitations"

    id = Column(String, primary_key=True, index=True, default=_uuid)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=True, index=True)
    employee_id = Column(String, ForeignKey("employees.id"), nullable=True, index=True)
    email = Column(String, nullable=False, index=True)
    token = Column(String, unique=True, index=True, nullable=False)
    role = Column(String, default=UserRole.EMPLOYEE.value)
    department = Column(String)
    job_title = Column(String)
    status = Column(String, default=InvitationStatus.PENDING.value, index=True)
    invited_by = Column(String, nullable=True)
    message = Column(Text, nullable=True)
    expires_at = Column(DateTime, nullable=False)
    accepted_at = Column(DateTime, nullable=True)
    reminder_count = Column(Integer, default=0)
    last_reminder_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ----------------------------------------------------------------------
# Workflow & orchestration
# ----------------------------------------------------------------------
class Workflow(Base):
    """A workflow run. One row per execution of a workflow template."""

    __tablename__ = "workflows"

    id = Column(String, primary_key=True, index=True, default=_uuid)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=True, index=True)
    employee_id = Column(String, ForeignKey("employees.id"), index=True)
    template_id = Column(String, nullable=True)
    name = Column(String, nullable=False)
    status = Column(String, default=WorkflowStatus.PENDING.value, index=True)
    current_stage = Column(String, nullable=True)
    progress = Column(Integer, default=0)
    state = Column(JSON, default=dict)
    context = Column(JSON, default=dict)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    employee = relationship("Employee", back_populates="workflows")
    tasks = relationship("Task", back_populates="workflow")
    execution_logs = relationship("ExecutionLog", back_populates="workflow")


class Agent(Base):
    __tablename__ = "agents"

    id = Column(String, primary_key=True, index=True, default=_uuid)
    name = Column(String, unique=True, nullable=False)
    role_description = Column(String)
    capabilities = Column(JSON, default=list)  # List of tools or skills
    is_active = Column(Boolean, default=True)
    total_executions = Column(Integer, default=0)
    successful_executions = Column(Integer, default=0)
    failed_executions = Column(Integer, default=0)
    avg_duration_seconds = Column(Float, default=0.0)
    last_active_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    tasks = relationship("Task", back_populates="assigned_agent")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, index=True, default=_uuid)
    workflow_id = Column(String, ForeignKey("workflows.id"), index=True)
    agent_id = Column(String, ForeignKey("agents.id"), nullable=True)
    agent_name = Column(String, nullable=True)
    task_key = Column(String, nullable=True, index=True)  # id from the workflow definition
    name = Column(String, nullable=False)
    description = Column(String)
    tool_name = Column(String, nullable=True)
    status = Column(String, default=TaskStatus.PENDING.value, index=True)
    priority = Column(Integer, default=0)
    dependencies = Column(JSON, default=list)
    input_data = Column(JSON, default=dict)
    result = Column(JSON, nullable=True)
    error_message = Column(String, nullable=True)
    retries = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    requires_approval = Column(Boolean, default=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    workflow = relationship("Workflow", back_populates="tasks")
    assigned_agent = relationship("Agent", back_populates="tasks")


class AgentExecution(Base):
    """One record per agent invocation - the agent-level audit trail."""

    __tablename__ = "agent_executions"

    id = Column(String, primary_key=True, index=True, default=_uuid)
    workflow_id = Column(String, index=True)
    task_id = Column(String, nullable=True, index=True)
    agent_name = Column(String, nullable=False, index=True)
    action = Column(String, nullable=False)
    status = Column(String, default="running", index=True)
    input_data = Column(JSON, default=dict)
    output_data = Column(JSON, default=dict)
    reasoning = Column(Text, nullable=True)
    llm_provider = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)
    attempt = Column(Integer, default=1)
    duration_seconds = Column(Float, default=0.0)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


class ExecutionLog(Base):
    __tablename__ = "execution_logs"

    id = Column(String, primary_key=True, index=True, default=_uuid)
    workflow_id = Column(String, ForeignKey("workflows.id"), index=True)
    task_id = Column(String, ForeignKey("tasks.id"), nullable=True)
    agent_id = Column(String, nullable=True)
    action = Column(String, nullable=False)
    level = Column(String, default="info")
    details = Column(JSON, default=dict)
    timestamp = Column(DateTime, default=datetime.utcnow)

    workflow = relationship("Workflow", back_populates="execution_logs")


class ExecutionPlan(Base):
    __tablename__ = "execution_plans"

    id = Column(String, primary_key=True, index=True, default=_uuid)
    workflow_id = Column(String, ForeignKey("workflows.id"), nullable=False, index=True)
    plan_data = Column(JSON, nullable=False)  # ExecutionPlanState serialized
    critical_path = Column(JSON, default=list)
    estimated_duration = Column(Integer, default=0)
    status = Column(String, default="generated")  # generated, active, completed, invalidated
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    workflow = relationship("Workflow")


class PlanningLog(Base):
    __tablename__ = "planning_logs"

    id = Column(String, primary_key=True, index=True, default=_uuid)
    workflow_id = Column(String, ForeignKey("workflows.id"), nullable=False, index=True)
    action = Column(String, nullable=False)
    reason = Column(String)
    details = Column(JSON, default=dict)
    timestamp = Column(DateTime, default=datetime.utcnow)

    workflow = relationship("Workflow")


class WorkflowTemplate(Base):
    __tablename__ = "workflow_templates"

    id = Column(String, primary_key=True, default=_uuid)
    organization_id = Column(String, nullable=True, index=True)
    key = Column(String, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    version = Column(String, default="1.0.0")
    definition = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ----------------------------------------------------------------------
# Compliance & documents
# ----------------------------------------------------------------------
class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, index=True, default=_uuid)
    organization_id = Column(String, nullable=True, index=True)
    employee_id = Column(String, ForeignKey("employees.id"), index=True)
    document_type = Column(String, nullable=False)  # e.g. "Offer Letter", "I-9 Form"
    file_name = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    file_size = Column(Integer, default=0)
    storage_path = Column(String, nullable=True)
    storage_url = Column(String, nullable=False)
    status = Column(String, default=DocumentStatus.UPLOADED.value, index=True)
    required = Column(Boolean, default=True)
    validation_errors = Column(JSON, default=list)
    extracted_data = Column(JSON, default=dict)
    expiry_date = Column(DateTime, nullable=True)
    verified_at = Column(DateTime, nullable=True)
    verified_by = Column(String, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    employee = relationship("Employee", back_populates="documents")


class VerificationReport(Base):
    __tablename__ = "verification_reports"

    id = Column(String, primary_key=True, default=_uuid)
    workflow_id = Column(String, nullable=False, index=True)
    employee_id = Column(String, nullable=True, index=True)
    overall_status = Column(String, nullable=False)
    confidence_score = Column(Float, default=0.0)
    missing_documents = Column(JSON, default=list)
    invalid_documents = Column(JSON, default=list)
    required_corrections = Column(JSON, default=list)
    compliance_findings = Column(JSON, default=list)
    warnings = Column(JSON, default=list)
    recommendations = Column(JSON, default=list)
    next_action = Column(String, default="WAIT")
    reasoning = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Approval(Base):
    __tablename__ = "approvals"

    id = Column(String, primary_key=True, index=True, default=_uuid)
    organization_id = Column(String, nullable=True, index=True)
    workflow_id = Column(String, nullable=False, index=True)
    task_id = Column(String, nullable=True, index=True)
    employee_id = Column(String, nullable=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    reason = Column(Text)
    status = Column(String, default=ApprovalStatus.PENDING.value, index=True)
    requested_by = Column(String, default="Manager Agent")
    required_role = Column(String, default=UserRole.HR.value)
    approver_id = Column(String, nullable=True)
    approver_email = Column(String, nullable=True)
    comments = Column(Text, nullable=True)
    payload = Column(JSON, default=dict)
    reminder_count = Column(Integer, default=0)
    last_reminder_at = Column(DateTime, nullable=True)
    escalated_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ----------------------------------------------------------------------
# Comms & audit
# ----------------------------------------------------------------------
class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String, primary_key=True, index=True, default=_uuid)
    organization_id = Column(String, nullable=True, index=True)
    user_id = Column(String, nullable=True, index=True)
    employee_id = Column(String, nullable=True, index=True)
    workflow_id = Column(String, nullable=True, index=True)
    type = Column(String, nullable=False)  # success | error | warning | info | approval
    category = Column(String, default="workflow")
    title = Column(String, nullable=False)
    message = Column(String, nullable=False)
    action_url = Column(String, nullable=True)
    metadata_json = Column(JSON, default=dict)
    is_read = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class EmailOutbox(Base):
    """Every outbound email is recorded here, whether or not SMTP actually delivered it."""

    __tablename__ = "email_outbox"

    id = Column(String, primary_key=True, index=True, default=_uuid)
    to_email = Column(String, nullable=False, index=True)
    subject = Column(String, nullable=False)
    body_text = Column(Text)
    body_html = Column(Text)
    template = Column(String, nullable=True)
    status = Column(String, default="queued", index=True)  # queued | sent | failed | simulated
    provider = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, index=True, default=_uuid)
    organization_id = Column(String, nullable=True, index=True)
    user_id = Column(String, nullable=True)
    actor = Column(String, nullable=True)  # human email or agent name
    actor_type = Column(String, default="system")  # user | agent | system
    action = Column(String, nullable=False, index=True)
    resource_type = Column(String, nullable=False, index=True)
    resource_id = Column(String, nullable=False, index=True)
    changes = Column(JSON, nullable=True)
    ip_address = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)


# Ordered list used by the SQL adapter and the seed script.
ALL_MODELS = [
    Organization,
    User,
    Employee,
    Invitation,
    Workflow,
    Agent,
    Task,
    AgentExecution,
    ExecutionLog,
    ExecutionPlan,
    PlanningLog,
    WorkflowTemplate,
    Document,
    VerificationReport,
    Approval,
    Notification,
    EmailOutbox,
    AuditLog,
]

TABLE_MODELS = {model.__tablename__: model for model in ALL_MODELS}
