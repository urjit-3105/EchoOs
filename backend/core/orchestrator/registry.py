from __future__ import annotations
from typing import Dict, Type, TYPE_CHECKING
if TYPE_CHECKING:
    from core.agents.base import BaseAgent
from core.logger.structured import get_logger

logger = get_logger(__name__)

class AgentRegistry:
    """
    Dynamic registry for all autonomous agents in the platform.
    Agents register themselves here, allowing the Orchestrator to dispatch work
    without hardcoding agent instances.
    """
    
    _instance = None
    _agents: Dict[str, BaseAgent] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AgentRegistry, cls).__new__(cls)
            cls._instance._agents = {}
        return cls._instance

    @classmethod
    def register(cls, name: str):
        """
        Decorator to register an agent class into the registry.
        Instantiates the agent and stores it.
        """
        def decorator(agent_class: Type[BaseAgent]):
            if name in cls._agents:
                logger.warning(f"Agent '{name}' is already registered. Overwriting.")
            cls._agents[name] = agent_class()
            logger.info(f"Registered agent: {name}")
            return agent_class
        return decorator

    @classmethod
    def get_agent(cls, name: str) -> BaseAgent:
        """
        Retrieve an agent instance by name.
        """
        if name not in cls._agents:
            raise ValueError(f"Agent '{name}' is not registered in the AgentRegistry.")
        return cls._agents[name]
        
    @classmethod
    def list_agents(cls) -> list[str]:
        return list(cls._agents.keys())
