from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
from core.state.models import ContextState, ExecutionPlanState
from core.orchestrator.service import OrchestratorService

router = APIRouter(prefix="/orchestrator", tags=["Orchestrator"])

@router.post("/start")
async def start_workflow(payload: Dict[str, Any]) -> Dict[str, str]:
    """
    Receives an ExecutionPlan and starts the workflow Orchestrator loop.
    In a real scenario, the payload would be parsed and validated into Pydantic models.
    """
    try:
        plan = ExecutionPlanState(**payload["plan"])
        context = ContextState(**payload["context"])
        workflow_id = await OrchestratorService.start_workflow(plan, context)
        return {"message": "Workflow started successfully.", "workflow_id": workflow_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/resume")
async def resume_workflow(workflow_id: str, action: str, details: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
    """
    Resumes a paused workflow (e.g., after a manual approval gate).
    """
    try:
        success = await OrchestratorService.resume_workflow(workflow_id, action, details or {})
        if success:
            return {"message": f"Workflow {workflow_id} resumed."}
        else:
            raise HTTPException(status_code=400, detail="Failed to resume workflow. Invalid action or state.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/cancel")
async def cancel_workflow(workflow_id: str) -> Dict[str, str]:
    """
    Cancels a running workflow.
    """
    try:
        success = await OrchestratorService.cancel_workflow(workflow_id)
        return {"message": f"Workflow {workflow_id} cancelled."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/status/{workflow_id}")
async def get_status(workflow_id: str) -> Dict[str, Any]:
    """
    Fetches the current status of the workflow execution plan.
    """
    status = await OrchestratorService.get_status(workflow_id)
    if not status:
        raise HTTPException(status_code=404, detail="Workflow not found.")
    return status

@router.get("/history/{workflow_id}")
async def get_history(workflow_id: str) -> Dict[str, Any]:
    """
    Fetches the event history and logs for a specific workflow.
    (Placeholder for Database querying)
    """
    return {"workflow_id": workflow_id, "history": []}
