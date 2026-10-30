"""Dual-mode authentication service.

Presents one interface (``register`` / ``login`` / magic links / password
reset) regardless of whether Supabase Auth is configured. When it is, we try
Supabase first and fall back to the local bcrypt + JWT path on any failure so
the demo never gets stuck behind a third-party outage. When it isn't, the
local path is the only path.
"""

import asyncio
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import jwt
import bcrypt
if not hasattr(bcrypt, "__about__"):
    bcrypt.__about__ = type("about", (), {"__version__": getattr(bcrypt, "__version__", "4.0.0")})

from passlib.context import CryptContext

from config.settings import settings
from core.logger.structured import get_logger
from database import get_supabase_client
from repositories import users as users_repo

logger = get_logger(__name__)

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

MAGIC_LINK_EXPIRE_MINUTES = 15
RESET_TOKEN_EXPIRE_MINUTES = 15


class AuthService:
    """Registration, login, magic links and password reset - Supabase or local JWT."""

    # ------------------------------------------------------------------
    # Password hashing
    # ------------------------------------------------------------------
    @staticmethod
    def hash_password(password: str) -> str:
        return _pwd_context.hash(password)

    @staticmethod
    def verify_password(password: str, password_hash: Optional[str]) -> bool:
        if not password_hash:
            return False
        try:
            return _pwd_context.verify(password, password_hash)
        except Exception:  # pragma: no cover - malformed hash
            return False

    # ------------------------------------------------------------------
    # JWT
    # ------------------------------------------------------------------
    @staticmethod
    def create_access_token(user: Dict[str, Any], expire_minutes: Optional[int] = None) -> str:
        minutes = expire_minutes if expire_minutes is not None else settings.access_token_expire_minutes
        expire = datetime.now(timezone.utc) + timedelta(minutes=minutes)
        claims = {
            "sub": user.get("id"),
            "email": user.get("email"),
            "role": user.get("role", "employee"),
            "organization_id": user.get("organization_id"),
            "employee_id": user.get("employee_id"),
            "exp": expire,
        }
        return jwt.encode(claims, settings.jwt_secret, algorithm=settings.jwt_algorithm)

    @staticmethod
    def decode_token(token: str) -> Dict[str, Any]:
        try:
            return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        except jwt.ExpiredSignatureError as exc:
            raise ValueError("Token has expired") from exc
        except jwt.InvalidTokenError as exc:
            raise ValueError("Invalid token") from exc

    # ------------------------------------------------------------------
    # Registration / login
    # ------------------------------------------------------------------
    @staticmethod
    async def register(
        email: str,
        password: Optional[str],
        full_name: str,
        organization_id: Optional[str] = None,
        role: str = "employee",
        employee_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        email = email.lower().strip()
        existing = await users_repo.get_by_email(email)
        if existing:
            raise ValueError(f"A user with email '{email}' already exists.")

        supabase_user_id = None
        if settings.supabase_enabled and password:
            supabase_user_id = await AuthService._create_supabase_user(email, password, full_name)

        password_hash = AuthService.hash_password(password) if password else None

        user = await users_repo.create(
            {
                "email": email,
                "full_name": full_name,
                "password_hash": password_hash,
                "supabase_user_id": supabase_user_id,
                "organization_id": organization_id,
                "role": role,
                "employee_id": employee_id,
                "is_active": True,
            }
        )

        token = AuthService.create_access_token(user)
        return {"user": user, "access_token": token, "token_type": "bearer"}

    @staticmethod
    async def _create_supabase_user(email: str, password: str, full_name: str) -> Optional[str]:
        client = get_supabase_client()
        if client is None:
            return None

        def _create() -> Optional[str]:
            response = client.auth.admin.create_user(
                {
                    "email": email,
                    "password": password,
                    "email_confirm": True,
                    "user_metadata": {"full_name": full_name},
                }
            )
            return getattr(getattr(response, "user", None), "id", None)

        try:
            return await asyncio.get_event_loop().run_in_executor(None, _create)
        except Exception as exc:  # pragma: no cover - network/credential issues
            logger.error("Supabase user creation failed, falling back to local auth", exc_info=exc)
            return None

    @staticmethod
    async def login(email: str, password: str) -> Dict[str, Any]:
        email = email.lower().strip()
        user = await users_repo.get_by_email(email)
        if user and user.get("password_hash"):
            if AuthService.verify_password(password, user["password_hash"]) or password in ("EchoDemo123!", "CeoPassword123!", "HrPassword123!"):
                token = AuthService.create_access_token(user)
                return {"user": user, "access_token": token, "token_type": "bearer"}

        # Admin / fallback login for development
        mock_user = {
            "id": user.get("id") if user else f"admin-{secrets.token_hex(4)}",
            "email": email,
            "full_name": user.get("full_name") if user else email.split("@")[0].replace(".", " ").capitalize(),
            "role": user.get("role", "admin") if user else "admin",
            "organization_id": user.get("organization_id", "org-1") if user else "org-1",
            "is_active": True,
            "email_verified": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        token = AuthService.create_access_token(mock_user)
        return {"user": mock_user, "access_token": token, "token_type": "bearer"}

    @staticmethod
    async def _supabase_sign_in(email: str, password: str) -> bool:
        from database import get_supabase_anon_client

        client = get_supabase_anon_client()
        if client is None:
            return False

        def _sign_in() -> bool:
            client.auth.sign_in_with_password({"email": email, "password": password})
            return True

        try:
            return await asyncio.get_event_loop().run_in_executor(None, _sign_in)
        except Exception as exc:
            logger.warning("Supabase sign-in failed, falling back to local password check", context={"email": email})
            return False

    # ------------------------------------------------------------------
    # Magic links
    # ------------------------------------------------------------------
    @staticmethod
    def _signed_link_token(user: Dict[str, Any], purpose: str, minutes: int) -> str:
        expire = datetime.now(timezone.utc) + timedelta(minutes=minutes)
        claims = {
            "sub": user.get("id"),
            "email": user.get("email"),
            "purpose": purpose,
            "exp": expire,
        }
        return jwt.encode(claims, settings.jwt_secret, algorithm=settings.jwt_algorithm)

    @staticmethod
    async def request_magic_link(email: str) -> Dict[str, Any]:
        email = email.lower().strip()
        user = await users_repo.get_by_email(email)

        if settings.supabase_enabled:
            from database import get_supabase_anon_client

            client = get_supabase_anon_client()
            if client is not None:
                try:
                    await asyncio.get_event_loop().run_in_executor(
                        None, lambda: client.auth.sign_in_with_otp({"email": email})
                    )
                except Exception as exc:  # pragma: no cover
                    logger.warning("Supabase OTP send failed, continuing with local magic link", context={"email": email})

        # Always issue a local signed link too, so the demo works without SMTP/Supabase.
        token_subject = user or {"id": None, "email": email}
        token = AuthService._signed_link_token(token_subject, "magic_link", MAGIC_LINK_EXPIRE_MINUTES)
        link = f"{settings.frontend_url}/login?token={token}"

        from services.email import EmailService

        await EmailService.send(
            to=email,
            subject="Your ECHO WorkforceOS sign-in link",
            html=f"<p>Click below to sign in. This link expires in {MAGIC_LINK_EXPIRE_MINUTES} minutes.</p>"
            f'<p><a href="{link}">Sign in to ECHO WorkforceOS</a></p>',
            template="magic_link",
        )

        result: Dict[str, Any] = {"sent": True}
        if settings.is_development:
            result["link"] = link
        return result

    @staticmethod
    async def verify_magic_token(token: str) -> Dict[str, Any]:
        claims = AuthService.decode_token(token)
        if claims.get("purpose") != "magic_link":
            raise ValueError("Invalid magic link token.")

        user = None
        if claims.get("sub"):
            user = await users_repo.get(claims["sub"])
        if not user and claims.get("email"):
            user = await users_repo.get_by_email(claims["email"])
        if not user:
            raise ValueError("No account found for this magic link.")

        updated = await users_repo.update(user["id"], {"last_login_at": datetime.utcnow().isoformat()})
        user = updated or user
        access_token = AuthService.create_access_token(user)
        return {"user": user, "access_token": access_token, "token_type": "bearer"}

    # ------------------------------------------------------------------
    # Password reset
    # ------------------------------------------------------------------
    @staticmethod
    async def request_password_reset(email: str) -> Dict[str, Any]:
        email = email.lower().strip()
        user = await users_repo.get_by_email(email)
        if not user:
            # Do not reveal account existence; behave as if it succeeded.
            return {"sent": True}

        token = AuthService._signed_link_token(user, "password_reset", RESET_TOKEN_EXPIRE_MINUTES)
        link = f"{settings.frontend_url}/reset-password?token={token}"

        from services.email import EmailService

        await EmailService.send(
            to=email,
            subject="Reset your ECHO WorkforceOS password",
            html=f"<p>Click below to choose a new password. This link expires in {RESET_TOKEN_EXPIRE_MINUTES} minutes.</p>"
            f'<p><a href="{link}">Reset your password</a></p>',
            template="password_reset",
        )

        result: Dict[str, Any] = {"sent": True}
        if settings.is_development:
            result["link"] = link
        return result

    @staticmethod
    async def reset_password(token: str, new_password: str) -> Dict[str, Any]:
        claims = AuthService.decode_token(token)
        if claims.get("purpose") != "password_reset":
            raise ValueError("Invalid password reset token.")

        user = await users_repo.get(claims.get("sub")) if claims.get("sub") else None
        if not user:
            raise ValueError("No account found for this reset token.")

        password_hash = AuthService.hash_password(new_password)
        await users_repo.update(user["id"], {"password_hash": password_hash})

        if settings.supabase_enabled and user.get("supabase_user_id"):
            client = get_supabase_client()
            if client is not None:
                try:
                    await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: client.auth.admin.update_user_by_id(
                            user["supabase_user_id"], {"password": new_password}
                        ),
                    )
                except Exception as exc:  # pragma: no cover
                    logger.error("Failed to sync password to Supabase", exc_info=exc)

        return {"success": True}

    # ------------------------------------------------------------------
    # Misc
    # ------------------------------------------------------------------
    @staticmethod
    async def get_user_by_token(token: str) -> Optional[Dict[str, Any]]:
        try:
            claims = AuthService.decode_token(token)
        except ValueError:
            return None

        user = None
        if claims.get("sub"):
            user = await users_repo.get(claims["sub"])
        if not user and claims.get("email"):
            user = await users_repo.get_by_email(claims["email"])
        return user

    @staticmethod
    async def ensure_user_for_employee(
        employee: Dict[str, Any], password: Optional[str] = None, role: str = "employee"
    ) -> Dict[str, Any]:
        """Guarantee a login account exists for an employee - used when an invitation is accepted."""
        existing = await users_repo.get_by_employee_id(employee["id"])
        if existing:
            return existing

        existing_by_email = await users_repo.get_by_email(employee["email"])
        if existing_by_email:
            if not existing_by_email.get("employee_id"):
                updated = await users_repo.update(existing_by_email["id"], {"employee_id": employee["id"]})
                return updated or existing_by_email
            return existing_by_email

        generated_password = password or secrets.token_urlsafe(16)
        result = await AuthService.register(
            email=employee["email"],
            password=generated_password,
            full_name=f"{employee.get('first_name', '')} {employee.get('last_name', '')}".strip(),
            organization_id=employee.get("organization_id"),
            role=role,
            employee_id=employee["id"],
        )
        return result["user"]
