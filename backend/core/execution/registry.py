from __future__ import annotations

from typing import Dict, Type, TYPE_CHECKING
from core.logger.structured import get_logger

if TYPE_CHECKING:
    # Import deferred to type-checking only: importing the concrete
    # `core.execution.plugins.base` submodule forces Python to initialise the
    # `core.execution.plugins` package, whose __init__ imports every plugin
    # module - each of which imports `ToolRegistry` from *this* module. Doing
    # that import eagerly here creates a circular import the moment any
    # plugin module is loaded before this file finishes executing.
    from core.execution.plugins.base import BasePlugin

logger = get_logger(__name__)

class ToolRegistry:
    """
    Dynamic registry for Enterprise Execution Plugins.
    """

    _instance = None
    _plugins: Dict[str, "BasePlugin"] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ToolRegistry, cls).__new__(cls)
            cls._instance._plugins = {}
        return cls._instance

    @classmethod
    def register(cls, name: str):
        """
        Decorator to register a plugin class into the registry.
        Instantiates the plugin and stores it.
        """
        def decorator(plugin_class: Type[BasePlugin]):
            if name in cls._plugins:
                logger.warning(f"Plugin '{name}' is already registered. Overwriting.")
            cls._plugins[name] = plugin_class()
            logger.info(f"Registered plugin: {name}")
            return plugin_class
        return decorator

    @classmethod
    def get_plugin(cls, name: str) -> BasePlugin:
        """
        Retrieve a plugin instance by name.
        """
        if name not in cls._plugins:
            raise ValueError(f"Plugin '{name}' is not registered in the ToolRegistry.")
        return cls._plugins[name]
        
    @classmethod
    def list_plugins(cls) -> list[str]:
        return list(cls._plugins.keys())
