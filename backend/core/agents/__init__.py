"""Importing this package registers every agent with the ``AgentRegistry``.

``main.py`` does ``import core.agents`` once at startup so every
``@AgentRegistry.register(...)`` decorator below actually runs.
"""

from typing import Any, Dict, List

# Import order matters only in that each module must run its own
# @AgentRegistry.register(...) decorator exactly once.
from core.agents import planner  # noqa: F401
from core.agents import execution  # noqa: F401
from core.agents import verification  # noqa: F401
from core.agents import monitoring  # noqa: F401
from core.agents import manager  # noqa: F401
from core.agents import mocks  # noqa: F401

from core.orchestrator.registry import AgentRegistry
from core.logger.structured import get_logger

logger = get_logger(__name__)

AGENT_CATALOG: List[Dict[str, Any]] = [
    {
        "name": "PlannerAgent",
        "display_name": "Planner Agent",
        "description": "Analyzes the workflow definition and generates an optimized DAG execution plan.",
        "capabilities": ["planning", "validation", "dependency_resolution"],
    },
    {
        "name": "ExecutionAgent",
        "display_name": "Execution Agent",
        "description": "Executes tasks against enterprise tool plugins (identity, storage, jira, slack, calendar, email).",
        "capabilities": ["tool_execution", "api_calls", "enterprise_plugins"],
    },
    {
        "name": "VerificationAgent",
        "display_name": "Verification Agent",
        "description": "Evaluates employee profile, documents and compliance policy against configurable rules.",
        "capabilities": ["document_verification", "compliance_checks", "policy_validation"],
    },
    {
        "name": "MonitoringAgent",
        "display_name": "Monitoring Agent",
        "description": "Health-checks provisioning tasks, retries recoverable failures and confirms completion.",
        "capabilities": [
            "health_check",
            "failure_detection",
            "retry_orchestration",
            "escalation",
            "completion_confirmation",
        ],
    },
    {
        "name": "ManagerAgent",
        "display_name": "Manager Agent",
        "description": "Human approval gate - auto-approves clean runs, escalates ambiguous ones to HR.",
        "capabilities": ["human_escalation", "approval_processing", "reminders", "policy_override"],
    },
    {
        "name": "NoOpAgent",
        "display_name": "No-Op Agent",
        "description": "Test double that always succeeds without side effects.",
        "capabilities": ["testing"],
    },
]


async def sync_agents_to_database() -> None:
    """Ensure every registered agent has a corresponding row in the ``agents`` table."""
    try:
        from repositories.agents import agents_repo
    except Exception as exc:  # noqa: BLE001 - repository package may not be wired up yet
        logger.error("Could not import agents repository.", context={"error": str(exc)})
        return

    for entry in AGENT_CATALOG:
        try:
            await agents_repo.ensure_registered(
                name=entry["name"],
                description=entry["description"],
                capabilities=entry["capabilities"],
            )
        except Exception as exc:  # noqa: BLE001 - one bad entry shouldn't block the others
            logger.error(
                "Failed to sync agent to database.",
                context={"agent": entry["name"], "error": str(exc)},
            )

    logger.info("Agent catalog synced to database.", context={"agents": AgentRegistry.list_agents()})
