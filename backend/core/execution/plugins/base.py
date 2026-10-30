from abc import ABC, abstractmethod
from typing import Dict, Any

class BasePlugin(ABC):
    """
    Abstract Base Class for all Enterprise Execution Plugins (Email, Slack, Jira, etc.).
    """

    @property
    @abstractmethod
    def tool_name(self) -> str:
        """Returns the unique identifier for this plugin (e.g., 'email', 'jira')."""
        pass

    @abstractmethod
    async def connect(self) -> bool:
        """Establishes connection/auth to the enterprise tool."""
        pass

    @abstractmethod
    async def validate(self, inputs: Dict[str, Any]) -> bool:
        """Validates the input parameters before execution."""
        pass

    @abstractmethod
    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Executes the core action. Must return a dict with a 'status' field."""
        pass

    @abstractmethod
    async def rollback(self, execution_data: Dict[str, Any]) -> bool:
        """Attempts to revert the action (e.g., delete a created ticket)."""
        pass

    @abstractmethod
    async def health(self) -> bool:
        """Checks if the external service is healthy."""
        pass
