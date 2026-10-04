"""
Authentication Router
JWT-based authentication for Admin endpoints
"""
import hmac
import os
import time
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from database.config import get_db
from services import ArticleService, AuditLogService
from security.rbac import (
    require_role,
    require_any_role,
    SUPER_ADMIN_ONLY,
    ADMIN_ONLY,
    ADMIN_OR_EDITOR,
    ANY_ROLE
)
from security.jwt import create_jwt_token, verify_jwt_token
from schemas import (
    Token,
    TokenPayload,
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse
)

router = APIRouter(prefix="/auth", tags=["authentication"])

security = HTTPBearer(auto_error=False)

# Admin credentials come ONLY from Render environment variables.
# No default passwords and no hardcoded demo accounts (fail-secure).
ENV_ADMIN_EMAIL = (os.getenv("ADMIN_EMAIL") or "").strip()
ENV_ADMIN_PASSWORD = (os.getenv("ADMIN_PASSWORD") or "").strip()
ENV_ADMIN_USERNAME = (os.getenv("ADMIN_USERNAME") or "").strip()

if not ENV_ADMIN_PASSWORD or not (ENV_ADMIN_EMAIL or ENV_ADMIN_USERNAME):
    print("WARNING: ADMIN_EMAIL/ADMIN_USERNAME/ADMIN_PASSWORD not set - admin login is disabled")

ADMIN_USER = {
    "id": "admin-env-uuid",
    "email": ENV_ADMIN_EMAIL,
    "username": ENV_ADMIN_USERNAME,
    "roles": ["ADMIN", "SUPER_ADMIN"],
    "full_name": ENV_ADMIN_USERNAME or "Admin",
}

# Kept (empty) only so the disabled register/create-admin routes below stay importable
USERS_DB: dict = {}

# --- Brute-force protection: max 5 failed logins per IP per 15 minutes (per server instance) ---
_FAILED: dict = {}
_MAX_FAILS = 5
_WINDOW = 15 * 60


def _blocked(ip: str) -> bool:
    now = time.time()
    recent = [t for t in _FAILED.get(ip, []) if now - t < _WINDOW]
    _FAILED[ip] = recent
    return len(recent) >= _MAX_FAILS


def _record_fail(ip: str) -> None:
    _FAILED.setdefault(ip, []).append(time.time())
    if len(_FAILED) > 5000:
        _FAILED.clear()


def _same(a: str, b: str) -> bool:
    return hmac.compare_digest(a.encode("utf-8"), b.encode("utf-8"))


def authenticate_user(identifier: str, password: str):
    """Constant-time check against the single admin defined in environment variables."""
    if not identifier or not password or not ENV_ADMIN_PASSWORD:
        return None

    identifier = identifier.strip()
    password = password.strip()

    # Email/username are matched case-insensitively (browsers and phones often change case)
    ident = identifier.lower()
    id_ok = False
    if ENV_ADMIN_EMAIL and _same(ident, ENV_ADMIN_EMAIL.lower()):
        id_ok = True
    if ENV_ADMIN_USERNAME and _same(ident, ENV_ADMIN_USERNAME.lower()):
        id_ok = True
    pw_ok = _same(password, ENV_ADMIN_PASSWORD)  # always evaluated

    return ADMIN_USER if (id_ok and pw_ok) else None


def create_access_token(user: dict) -> Token:
    """
    Create access token for authenticated user.
    """
    jwt_token = create_jwt_token(
        user_id=user["id"],
        email=user["email"],
        roles=user["roles"]
    )
    
    return Token(access_token=jwt_token, token_type="Bearer", expires_in=86400)


@router.post("/login", response_model=LoginResponse)
async def login(
    credentials: LoginRequest,
    request: Request,
    db=Depends(get_db)
):
    """
    Login endpoint for authentication.
    """
    ip = (request.headers.get("x-forwarded-for", "").split(",")[0].strip()
          or (request.client.host if request.client else "unknown"))

    if _blocked(ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed attempts. Please try again in 15 minutes.",
        )

    user = authenticate_user(credentials.email, credentials.password)

    if not user:
        _record_fail(ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token = create_access_token(user)

    return LoginResponse(
        token=token,
        user={
            "id": user["id"],
            "email": user["email"],
            "roles": user["roles"],
            "full_name": user.get("full_name", "Admin")
        }
    )


@router.post("/register", status_code=status.HTTP_403_FORBIDDEN)
async def register(request: RegisterRequest):
    """Public registration is disabled (single-admin site)."""
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Registration is disabled")


@router.get("/me", response_model=dict)
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get current authenticated user.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )

    payload = verify_jwt_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return {
        "id": payload.get("sub"),
        "email": payload.get("email"),
        "roles": payload.get("roles", [])
    }


@router.get("/me/permissions")
async def get_user_permissions(
    user: dict = Depends(get_current_user)
):
    """
    Get current user's permissions based on roles.
    """
    roles = user.get("roles", [])

    permissions = {
        "SUPER_ADMIN": "SUPER_ADMIN" in roles,
        "ADMIN": "ADMIN" in roles,
        "EDITOR": "EDITOR" in roles,
        "can_create_articles": "ADMIN" in roles or "EDITOR" in roles,
        "can_publish_articles": "ADMIN" in roles or "SUPER_ADMIN" in roles,
        "can_delete_articles": "ADMIN" in roles or "SUPER_ADMIN" in roles,
        "can_manage_users": "SUPER_ADMIN" in roles,
        "can_view_audits": "ADMIN" in roles or "SUPER_ADMIN" in roles,
        "can_manage_storage": "ADMIN" in roles or "SUPER_ADMIN" in roles,
    }

    return permissions


@router.get("/admin/protected")
async def admin_protected(user: dict = Depends(ADMIN_ONLY)):
    return {
        "message": "Welcome, Admin!",
        "user_email": user.get("email"),
        "user_roles": user.get("roles", [])
    }


@router.get("/editor/protected")
async def editor_protected(user: dict = Depends(ADMIN_OR_EDITOR)):
    return {
        "message": "Welcome, Admin or Editor!",
        "user_email": user.get("email"),
        "user_roles": user.get("roles", [])
    }


@router.get("/super-admin/protected")
async def super_admin_protected(user: dict = Depends(SUPER_ADMIN_ONLY)):
    return {
        "message": "Welcome, Super Admin!",
        "user_email": user.get("email"),
        "user_roles": user.get("roles", [])
    }


@router.post("/super-admin/create-admin", status_code=status.HTTP_403_FORBIDDEN)
async def create_admin_user():
    """Disabled: extra admins are not supported (admin is defined via environment variables)."""
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not supported")
