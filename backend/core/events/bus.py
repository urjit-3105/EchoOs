import asyncio
from enum import Enum
from typing import Callable, Dict, Any, List
from core.logger.structured import get_logger

logger = get_logger(__name__)

class EventType(str, Enum):
    EmployeeCreated = "EmployeeCreated"
    DocumentsUploaded = "DocumentsUploaded"
    VerificationCompleted = "VerificationCompleted"
    CompliancePassed = "CompliancePassed"
    ProvisioningStarted = "ProvisioningStarted"
    WorkflowCompleted = "WorkflowCompleted"
    WorkflowFailed = "WorkflowFailed"

class EventBus:
    """
    An in-memory Pub/Sub event bus using asyncio.
    Can be easily extended to use Redis or Kafka for distributed events.
    """
    
    _subscribers: Dict[str, List[Callable]] = {}

    @classmethod
    def subscribe(cls, event_type: str, handler: Callable):
        """
        Subscribe to an event.
        """
        if event_type not in cls._subscribers:
            cls._subscribers[event_type] = []
        cls._subscribers[event_type].append(handler)
        logger.debug(f"Subscribed handler {handler.__name__} to event: {event_type}")

    @classmethod
    async def publish(cls, event_type: str, payload: Dict[str, Any]):
        """
        Publish an event to all subscribers asynchronously.
        """
        logger.info(f"Publishing event: {event_type}", context={"payload": payload})
        
        if event_type not in cls._subscribers:
            logger.debug(f"No subscribers for event: {event_type}")
            return
            
        handlers = cls._subscribers[event_type]
        tasks = []
        
        import inspect
        for handler in handlers:
            if inspect.iscoroutinefunction(handler):
                tasks.append(asyncio.create_task(handler(payload)))
            else:
                # Run synchronous handlers in the executor
                loop = asyncio.get_event_loop()
                tasks.append(loop.run_in_executor(None, handler, payload))
                
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
