from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from core.state.models import ContextState, VerificationReportState
from core.verification.engine import DecisionEngine
from core.verification.rules import RuleEngine

router = APIRouter(prefix="/verification", tags=["Verification"])

@router.post("/validate")
async def validate_context(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Synchronously runs the validation engine against a specific ContextState.
    """
    try:
        context = ContextState(**payload)
        report = DecisionEngine.evaluate(context)
        return report.model_dump()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/report/{workflow_id}")
async def get_report(workflow_id: str) -> Dict[str, Any]:
    """
    Placeholder to fetch a saved VerificationReport from the database.
    """
    return {"workflow_id": workflow_id, "status": "Not Implemented (Requires DB Layer)"}

@router.get("/rules")
async def get_rules() -> Dict[str, Any]:
    """
    Fetches the active compliance rules.
    """
    if not RuleEngine._rules:
        RuleEngine.load_rules()
    return RuleEngine._rules
