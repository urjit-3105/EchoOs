"""Human-in-the-loop approval gates."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException

from core.logger.structured import get_logger
from repositories import approvals as approvals_repo
from schemas import ApprovalDecision
from services.approvals import ApprovalService

logger = get_logger(__name__)

router = APIRouter(prefix="/approvals", tags=["Approvals"])


@router.get("/")
async def list_approvals(status: Optional[str] = None, organization_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """List approvals, optionally filtered by status/organization."""
    filters: Dict[str, Any] = {}
    if status:
        filters["status"] = status
    if organization_id:
        filters["organization_id"] = organization_id
    return await approvals_repo.list(order_by="created_at", descending=True, **filters)


@router.get("/pending")
async def list_pending_approvals(organization_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Approvals awaiting a decision."""
    return await ApprovalService.list_pending(organization_id)


@router.get("/{approval_id}")
async def get_approval(approval_id: str) -> Dict[str, Any]:
    """Fetch one approval by id."""
    approval = await ApprovalService.get(approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail=f"Approval '{approval_id}' not found.")
    return approval


@router.post("/{approval_id}/decision")
async def decide_approval(approval_id: str, payload: ApprovalDecision) -> Dict[str, Any]:
    """Approve or reject the request - resumes the workflow via the ApprovalResolved event."""
    try:
        return await ApprovalService.resolve(
            approval_id,
            approved=payload.approved,
            approver_email=payload.approver_email,
            approver_id=payload.approver_id,
            comments=payload.comments,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{approval_id}/remind")
async def remind_approval(approval_id: str) -> Dict[str, Any]:
    """Send an additional reminder to the approvers."""
    approval = await ApprovalService.get(approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail=f"Approval '{approval_id}' not found.")
    updated = await ApprovalService.send_reminder(approval)
    return updated or approval


@router.post("/{approval_id}/escalate")
async def escalate_approval(approval_id: str) -> Dict[str, Any]:
    """Force-escalate an approval."""
    approval = await ApprovalService.get(approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail=f"Approval '{approval_id}' not found.")
    updated = await ApprovalService.escalate(approval)
    return updated or approval
