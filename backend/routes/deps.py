"""Shared FastAPI dependencies used across every route module.

Centralises authentication (JWT bearer decoding via ``AuthService``), role
enforcement, organization resolution and pagination so individual route
modules stay thin and consistent.
"""

from typing import Any, Dict, Optional

from fastapi import Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from core.logger.structured import get_logger
from repositories import organizations as organizations_repo
from services.auth import AuthService

logger = get_logger(__name__)

security = HTTPBearer(auto_error=False)


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[Dict[str, Any]]:
    """Decode the bearer token's JWT claims when present; ``None`` when absent or invalid.

    Used by read endpoints so the demo can be browsed without logging in first
    (see ``settings.is_development``), while still identifying the caller when
    a token is supplied.
    """
    if credentials is None or not credentials.credentials:
        return None
    try:
        return AuthService.decode_token(credentials.credentials)
    except ValueError:
        return None


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Dict[str, Any]:
    """Decode the bearer token's JWT claims; raises 401 when missing or invalid."""
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        return AuthService.decode_token(credentials.credentials)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


def require_roles(*roles: str):
    """Dependency factory: 403s unless the caller's role is one of ``roles``.

    ``admin`` always satisfies every role check.
    """

    async def _checker(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        role = (user.get("role") or "employee").lower()
        allowed = {r.lower() for r in roles}
        if role != "admin" and role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of roles {sorted(allowed)}; caller has '{role}'.",
            )
        return user

    return _checker


async def get_current_org(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """The caller's organization, falling back to the single default org.

    Raises 404 only when no organization exists at all.
    """
    org = None
    org_id = user.get("organization_id")
    if org_id:
        org = await organizations_repo.get(org_id)
    if not org:
        org = await organizations_repo.get_default()
    if not org:
        raise HTTPException(status_code=404, detail="No organization exists yet.")
    return org


async def resolve_org_id(
    organization_id: Optional[str] = Query(None, description="Explicit organization id filter."),
    user: Optional[Dict[str, Any]] = Depends(get_optional_user),
) -> Optional[str]:
    """The explicit query param wins; otherwise the authenticated user's org; otherwise ``None``."""
    if organization_id:
        return organization_id
    if user:
        return user.get("organization_id")
    return None


class PaginationParams:
    """Common ``limit``/``offset`` query parameters."""

    def __init__(
        self,
        limit: int = Query(50, ge=1, le=500, description="Max rows to return."),
        offset: int = Query(0, ge=0, description="Rows to skip."),
    ):
        self.limit = limit
        self.offset = offset
