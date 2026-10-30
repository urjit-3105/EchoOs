"""Repository singletons - the only objects services should import.

Every module in this package exposes one pre-instantiated repository so the
rest of the codebase never has to know a table name or construct a
repository itself.
"""

from repositories.agent_executions import agent_executions
from repositories.agents import agents_repo
from repositories.approvals import approvals
from repositories.audit import audit_logs
from repositories.documents import documents
from repositories.email_outbox import email_outbox
from repositories.employees import employees
from repositories.execution_logs import execution_logs
from repositories.execution_plans import execution_plans
from repositories.invitations import invitations
from repositories.notifications import notifications
from repositories.organizations import organizations
from repositories.tasks import tasks
from repositories.users import users
from repositories.verification_reports import verification_reports
from repositories.workflow_templates import workflow_templates
from repositories.workflows import workflows

__all__ = [
    "organizations",
    "users",
    "employees",
    "invitations",
    "workflows",
    "tasks",
    "documents",
    "approvals",
    "notifications",
    "audit_logs",
    "agents_repo",
    "agent_executions",
    "execution_plans",
    "execution_logs",
    "verification_reports",
    "email_outbox",
    "workflow_templates",
]
