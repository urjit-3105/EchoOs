from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from core.state.models import ContextState
from core.logger.structured import get_logger

logger = get_logger(__name__)

class BaseAgent(ABC):
    """
    The abstract base class for all autonomous AI agents in the platform.
    Enforces a strict execution lifecycle and state management.
    """
    
    def __init__(self, name: str, capabilities: list[str] = None):
        self.name = name
        self.capabilities = capabilities or []
        self.logger = get_logger(f"agent.{self.name.lower().replace(' ', '_')}")

    @abstractmethod
    async def execute(self, context: ContextState) -> Dict[str, Any]:
        """
        The core execution logic of the agent.
        Takes in a unified ContextState and returns a dictionary of output data.
        """
        pass

    @abstractmethod
    async def validate(self, context: ContextState) -> bool:
        """
        Validates whether the agent has all required data in the context to execute safely.
        """
        pass

    async def update_state(self, context: ContextState, result: Dict[str, Any]) -> None:
        """
        Optional hook to mutate or update external states, although usually the WorkflowEngine
        handles the state update utilizing the returned output from `execute()`.
        """
        pass

    async def emit_event(self, event_name: str, payload: Dict[str, Any]) -> None:
        """
        Publishes an event to the EventBus.
        """
        self.logger.info(f"Emitting event: {event_name}", context=payload)
        from core.events.bus import EventBus
        await EventBus.publish(event_name, payload)

    def log_execution(self, action: str, details: Dict[str, Any] = None) -> None:
        """
        Structured logging wrapper for the agent.
        """
        self.logger.info(action, context=details)

    @abstractmethod
    async def recover(self, context: ContextState, error: Exception) -> Dict[str, Any]:
        """
        Fallback logic when `execute()` throws an exception.
        Should attempt self-healing or return an escalated error state.
        """
        pass

    async def run(self, context: ContextState) -> Dict[str, Any]:
        """
        The template method that executes the full lifecycle of the agent.
        Do NOT override this method.
        """
        self.log_execution("started", {"task_id": context.current_task.task_id})
        
        try:
            if not await self.validate(context):
                raise ValueError(f"Agent {self.name} failed validation.")
            
            result = await self.execute(context)
            await self.update_state(context, result)
            self.log_execution("completed", {"result": result})
            return result
            
        except Exception as e:
            self.logger.error("Execution failed", exc_info=e)
            return await self.recover(context, e)
