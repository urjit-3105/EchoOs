from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from core.state.models import TaskState
from core.execution.engine import ExecutionPipeline
from core.execution.registry import ToolRegistry

router = APIRouter(prefix="/execution", tags=["Execution"])

@router.post("/run")
async def run_task(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Test endpoint to synchronously run an execution task.
    """
    try:
        task = TaskState(**payload)
        result = await ExecutionPipeline.run(task)
        if result.get("status") == "failed":
            raise HTTPException(status_code=400, detail=result)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/rollback")
async def rollback_task(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Test endpoint to synchronously rollback an execution task.
    """
    try:
        task = TaskState(**payload)
        result = await ExecutionPipeline.rollback(task)
        if result.get("status") == "failed":
            raise HTTPException(status_code=400, detail=result)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/plugins")
async def list_plugins() -> Dict[str, list[str]]:
    """
    Returns the list of dynamically registered enterprise tools.
    """
    return {"plugins": ToolRegistry.list_plugins()}

@router.get("/history/{workflow_id}")
async def get_history(workflow_id: str) -> Dict[str, Any]:
    """
    Placeholder for fetching tool execution history.
    """
    return {"workflow_id": workflow_id, "history": []}
