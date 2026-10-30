"""Test doubles only.

``ExecutionAgent``, ``MonitoringAgent`` and ``ManagerAgent`` are now real
implementations (see ``core/agents/execution.py``, ``core/agents/monitoring.py``
and ``core/agents/manager.py``) and register themselves under those same
names, so the duplicates that used to live here have been removed - keeping
both around meant whichever module imported last silently won the
registration. This module now only holds agents that exist purely for tests
and never clash with a production agent name.
"""

from typing import Any, Dict

from core.agents.base import BaseAgent
from core.orchestrator.registry import AgentRegistry
from core.state.models import ContextState


@AgentRegistry.register("NoOpAgent")
class NoOpAgent(BaseAgent):
    """Does nothing and always succeeds - useful for exercising orchestrator plumbing in tests."""

    def __init__(self):
        super().__init__(name="No-Op Agent", capabilities=["testing"])

    async def validate(self, context: ContextState) -> bool:
        return True

    async def execute(self, context: ContextState) -> Dict[str, Any]:
        self.logger.info("NoOpAgent executing...", context={"task": context.current_task.name})
        return {"status": "success", "result": "no-op"}

    async def recover(self, context: ContextState, error: Exception) -> Dict[str, Any]:
        return {"status": "failed", "error": str(error)}
