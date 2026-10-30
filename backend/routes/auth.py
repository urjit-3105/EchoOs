"""Authentication endpoints - registration, login, magic links, password reset."""

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException

from core.logger.structured import get_logger
from models.database import UserRole
from repositories import users as users_repo
from routes.deps import get_current_user
from schemas import (
    LoginRequest,
    MagicLinkRequest,
    MagicLinkVerifyRequest,
    MessageResponse,
    PasswordResetConfirm,
    PasswordResetRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from services.auth import AuthService

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse)
async def register(payload: RegisterRequest) -> Dict[str, Any]:
    """Create a new user account and return an access token."""
    try:
        return await AuthService.register(
            email=payload.email,
            password=payload.password,
            full_name=payload.full_name,
            organization_id=payload.organization_id,
            role=payload.role,
            employee_id=payload.employee_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest) -> Dict[str, Any]:
    """Authenticate with email + password and return an access token."""
    try:
        return await AuthService.login(payload.email, payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.post("/magic-link", response_model=MessageResponse)
async def request_magic_link(payload: MagicLinkRequest) -> Dict[str, Any]:
    """Send (or simulate) a passwordless sign-in link."""
    result = await AuthService.request_magic_link(payload.email)
    message = "Magic link sent." if result.get("sent") else "Failed to send magic link."
    return {"message": message, "success": bool(result.get("sent")), **({"link": result["link"]} if "link" in result else {})}


@router.post("/magic-link/verify", response_model=TokenResponse)
async def verify_magic_link(payload: MagicLinkVerifyRequest) -> Dict[str, Any]:
    """Exchange a magic-link token for an access token."""
    try:
        return await AuthService.verify_magic_token(payload.token)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/password-reset", response_model=MessageResponse)
async def request_password_reset(payload: PasswordResetRequest) -> Dict[str, Any]:
    """Send (or simulate) a password reset link. Never reveals account existence."""
    result = await AuthService.request_password_reset(payload.email)
    return {"message": "If the account exists, a reset link was sent.", "success": bool(result.get("sent"))}


@router.post("/password-reset/confirm", response_model=MessageResponse)
async def confirm_password_reset(payload: PasswordResetConfirm) -> Dict[str, Any]:
    """Set a new password using a password-reset token."""
    try:
        await AuthService.reset_password(payload.token, payload.new_password)
        return {"message": "Password updated.", "success": True}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/me", response_model=UserResponse)
async def me(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """The authenticated user's profile."""
    user_id = user.get("sub")
    row = await users_repo.get(user_id) if user_id else None
    if not row:
        return {
            "id": user_id or "admin-user",
            "email": user.get("email", "admin@echo-workforceos.com"),
            "full_name": user.get("email", "Admin").split("@")[0].capitalize(),
            "role": user.get("role", "admin"),
            "is_active": True,
            "email_verified": True,
            "organization_id": user.get("organization_id", "org-1"),
        }
    return row


@router.post("/logout", response_model=MessageResponse)
async def logout() -> Dict[str, Any]:
    """Stateless JWT logout - the client discards its token; nothing to revoke server-side."""
    return {"message": "Logged out.", "success": True}


@router.get("/roles")
async def roles() -> List[str]:
    """The role catalogue used throughout the platform."""
    return [role.value for role in UserRole]
