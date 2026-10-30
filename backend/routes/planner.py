from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List
from core.state.models import ContextState
from core.agents.planner import PlannerAgent

router = APIRouter(prefix="/planner", tags=["Planner"])

# A singleton or dependency-injected agent for the route
planner_agent = PlannerAgent()

@router.post("/plan")
async def generate_plan(context: ContextState) -> Dict[str, Any]:
    """
    Ingests a workflow context and returns an optimized DAG Execution Plan.
    """
    result = await planner_agent.run(context)
    if result.get("status") == "failed":
        raise HTTPException(status_code=400, detail=result)
    return result

@router.post("/validate")
async def validate_workflow(context: ContextState) -> Dict[str, Any]:
    """
    Pre-flights a workflow context for missing documents, approvals, or definition errors.
    """
    try:
        from core.planner.validator import WorkflowValidator
        WorkflowValidator.validate(context, context.workflow_definition)
        return {"valid": True, "message": "Workflow is valid."}
    except Exception as e:
        raise HTTPException(status_code=400, detail={"valid": False, "error": str(e)})

@router.get("/workflows")
async def list_workflows() -> List[Dict[str, Any]]:
    """
    Returns a list of active workflows currently being managed by the system.
    (Placeholder: Would query DB in production)
    """
    return [
        {"workflow_id": "wf-101", "status": "running"},
        {"workflow_id": "wf-102", "status": "paused"}
    ]

@router.get("/templates")
async def list_templates() -> List[Dict[str, Any]]:
    """
    Returns available Workflow Templates that can be fed into the Planner.
    (Placeholder: Would query DB in production)
    """
    return [
        {"id": "tpl-001", "name": "Employee Onboarding"},
        {"id": "tpl-002", "name": "Employee Offboarding"},
        {"id": "tpl-003", "name": "Vendor Approval"}
    ]
