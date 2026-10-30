"""Employee invitations: create, list, resend, revoke, QR codes, public accept flow."""

import base64
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Response

from core.logger.structured import get_logger
from repositories import invitations as invitations_repo
from routes.deps import PaginationParams, get_current_user
from schemas import InvitationAcceptRequest, InvitationCreate
from services.invitations import InvitationService

logger = get_logger(__name__)

router = APIRouter(prefix="/invitations", tags=["Invitations"])


@router.get("/")
async def list_invitations(
    organization_id: Optional[str] = None,
    status: Optional[str] = None,
    pagination: PaginationParams = Depends(),
) -> Dict[str, Any]:
    """List invitations, optionally filtered by organization/status."""
    filters: Dict[str, Any] = {}
    if organization_id:
        filters["organization_id"] = organization_id
    if status:
        filters["status"] = status
    rows = await invitations_repo.list(order_by="created_at", descending=True, **filters)
    total = len(rows)
    page = rows[pagination.offset : pagination.offset + pagination.limit]
    return {"items": page, "total": total, "limit": pagination.limit, "offset": pagination.offset}


@router.post("/")
async def create_invitation(
    payload: InvitationCreate, user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Invite an employee - creates the employee record (if needed), the invitation and sends the email."""
    try:
        return await InvitationService.create(
            email=payload.email,
            first_name=payload.first_name,
            last_name=payload.last_name,
            organization_id=payload.organization_id,
            role=payload.role,
            department=payload.department,
            job_title=payload.job_title,
            invited_by=payload.invited_by or user.get("email"),
            message=payload.message,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/token/{token}")
async def get_invitation_by_token(token: str) -> Dict[str, Any]:
    """PUBLIC - resolve an invitation (+ employee + organization) by its token."""
    bundle = await InvitationService.get_by_token(token)
    if not bundle:
        raise HTTPException(status_code=404, detail="Invitation not found.")
    if bundle["invitation"].get("status") == "expired":
        raise HTTPException(status_code=410, detail="This invitation has expired.")
    return bundle


@router.post("/token/{token}/accept")
async def accept_invitation(token: str, payload: InvitationAcceptRequest) -> Dict[str, Any]:
    """PUBLIC - accept an invitation, optionally setting a password and profile fields."""
    try:
        return await InvitationService.accept(token, password=payload.password, profile=payload.profile)
    except ValueError as exc:
        detail = str(exc)
        status_code = 410 if "expired" in detail.lower() else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc


@router.post("/{invitation_id}/resend")
async def resend_invitation(invitation_id: str) -> Dict[str, Any]:
    """Resend the invitation email and bump the reminder counter."""
    updated = await InvitationService.resend(invitation_id)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Invitation '{invitation_id}' not found.")
    return updated


@router.post("/{invitation_id}/revoke")
async def revoke_invitation(invitation_id: str) -> Dict[str, Any]:
    """Revoke a pending invitation."""
    updated = await InvitationService.revoke(invitation_id)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Invitation '{invitation_id}' not found.")
    return updated


@router.get("/{invitation_id}/qr")
async def invitation_qr(invitation_id: str) -> Dict[str, str]:
    """QR code for the invitation's accept URL as a base64 data URL."""
    invitation = await invitations_repo.get(invitation_id)
    if not invitation:
        raise HTTPException(status_code=404, detail=f"Invitation '{invitation_id}' not found.")
    accept_url = InvitationService.accept_url(invitation["token"])
    return {"qr_code": InvitationService.qr_code_data_url(accept_url)}


@router.get("/{invitation_id}/qr.png")
async def invitation_qr_png(invitation_id: str) -> Response:
    """Raw PNG QR code for the invitation's accept URL, for embedding or printing."""
    invitation = await invitations_repo.get(invitation_id)
    if not invitation:
        raise HTTPException(status_code=404, detail=f"Invitation '{invitation_id}' not found.")

    accept_url = InvitationService.accept_url(invitation["token"])
    data_url = InvitationService.qr_code_data_url(accept_url)
    if not data_url:
        raise HTTPException(status_code=503, detail="QR code generation is unavailable (qrcode package not installed).")

    _, _, encoded = data_url.partition(",")
    png_bytes = base64.b64decode(encoded)
    return Response(content=png_bytes, media_type="image/png")
