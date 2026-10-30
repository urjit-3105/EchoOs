from typing import Callable, Dict, Any
from core.logger.structured import get_logger

logger = get_logger(__name__)

class ToolRegistry:
    """
    Centralized registry for enterprise tools (e.g., Gmail, Slack, Jira, OCR).
    Agents request tools from this registry rather than instantiating them directly.
    """
    
    _instance = None
    _tools: Dict[str, Callable] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ToolRegistry, cls).__new__(cls)
            cls._instance._tools = {}
        return cls._instance

    @classmethod
    def register(cls, name: str) -> Callable:
        """
        Decorator to register a tool function into the registry.
        """
        def decorator(func: Callable):
            if name in cls._tools:
                logger.warning(f"Tool '{name}' is already registered. Overwriting.")
            cls._tools[name] = func
            logger.info(f"Registered tool: {name}")
            return func
        return decorator

    @classmethod
    def get_tool(cls, name: str) -> Callable:
        """
        Retrieve a tool by name.
        """
        if name not in cls._tools:
            raise ValueError(f"Tool '{name}' is not registered.")
        return cls._tools[name]

    @classmethod
    async def execute_tool(cls, name: str, **kwargs) -> Any:
        """
        Execute a registered tool asynchronously.
        """
        tool = cls.get_tool(name)
        logger.info(f"Executing tool: {name}", context={"kwargs": kwargs})
        
        try:
            # Check if it's an async function (in real implementation, inspect.iscoroutinefunction)
            import inspect
            if inspect.iscoroutinefunction(tool):
                return await tool(**kwargs)
            else:
                return tool(**kwargs)
        except Exception as e:
            logger.error(f"Tool '{name}' execution failed.", exc_info=e)
            raise


# --- Placeholder Enterprise Tools ---

@ToolRegistry.register("gmail_send_email")
async def gmail_send_email(to: str, subject: str, body: str) -> bool:
    logger.info(f"Mock sending email to {to}")
    return True

@ToolRegistry.register("slack_post_message")
async def slack_post_message(channel: str, message: str) -> bool:
    logger.info(f"Mock posting to slack channel {channel}")
    return True

@ToolRegistry.register("jira_create_ticket")
async def jira_create_ticket(title: str, description: str, assignee: str) -> str:
    logger.info(f"Mock creating Jira ticket for {assignee}")
    return "IT-101"

@ToolRegistry.register("ocr_extract_text")
async def ocr_extract_text(document_url: str) -> str:
    logger.info(f"Mock extracting text from {document_url}")
    return "Extracted text content from OCR."
