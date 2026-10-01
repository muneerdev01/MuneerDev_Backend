"""
Authentication Router
JWT-based authentication for Admin endpoints
"""
import os
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Body
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

# Render Environment Variables se Dynamic Credentials load karen
ENV_ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "muneer.dev01@gmail.com")
ENV_ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "000000")
ENV_ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "Admin1")

# In-Memory Database synced with Render Environment Variables
USERS_DB = {
    ENV_ADMIN_EMAIL: {
        "id": "admin-env-uuid",
        "email": ENV_ADMIN_EMAIL,
        "username": ENV_ADMIN_USERNAME,
        "password": ENV_ADMIN_PASSWORD,
        "roles": ["ADMIN", "SUPER_ADMIN"],
        "full_name": ENV_ADMIN_USERNAME
    },
    "superadmin@example.com": {
        "id": "super-admin-uuid",
        "email": "superadmin@example.com",
        "username": "superadmin",
        "password": "superadmin123",
        "roles": ["SUPER_ADMIN"],
        "full_name": "Super Admin"
    },
    "admin@example.com": {
        "id": "admin-uuid",
        "email": "admin@example.com",
        "username": "admin",
        "password": "admin123",
        "roles": ["ADMIN"],
        "full_name": "Admin User"
    }
}


def authenticate_user(identifier: str, password: str) -> dict:
    """
    Authenticate user against email, username, or hardcoded Render environment settings.
    """
    if not identifier or not password:
        return None

    # Clean input whitespace
    identifier = identifier.strip()
    password = password.strip()

    user = None

    # 1. Direct Email Lookup
    if identifier in USERS_DB:
        user = USERS_DB[identifier]
    else:
        # 2. Username Match (e.g. Admin1 or ENV_ADMIN_EMAIL)
        for u in USERS_DB.values():
            if u.get("username") == identifier or u.get("email") == identifier:
                user = u
                break

    # Fallback Direct Check for Env Variables
    if not user:
        if (identifier == ENV_ADMIN_EMAIL or identifier == ENV_ADMIN_USERNAME) and password == ENV_ADMIN_PASSWORD:
            return {
                "id": "admin-env-uuid",
                "email": ENV_ADMIN_EMAIL,
                "roles": ["ADMIN", "SUPER_ADMIN"],
                "full_name": ENV_ADMIN_USERNAME
            }

    if not user:
        return None

    # Password Verification
    if user.get("password") != password:
        return None

    return user


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
    db=Depends(get_db)
):
    """
    Login endpoint for authentication.
    """
    # Accept input from email field (which can contain email or username)
    user = authenticate_user(credentials.email, credentials.password)

    if not user:
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


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest):
    """
    Register a new user.
    """
    if request.email in USERS_DB:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    new_user = {
        "id": f"user-{len(USERS_DB) + 1}",
        "email": request.email,
        "password": request.password,
        "roles": ["EDITOR"],
        "full_name": request.full_name or request.email.split("@")[0]
    }

    USERS_DB[request.email] = new_user

    return RegisterResponse(
        message="User registered successfully",
        user={
            "id": new_user["id"],
            "email": new_user["email"],
            "roles": new_user["roles"],
            "full_name": new_user.get("full_name")
        }
    )


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
async def admin_protected(user: dict = ADMIN_ONLY):
    return {
        "message": "Welcome, Admin!",
        "user_email": user.get("email"),
        "user_roles": user.get("roles", [])
    }


@router.get("/editor/protected")
async def editor_protected(user: dict = ADMIN_OR_EDITOR):
    return {
        "message": "Welcome, Admin or Editor!",
        "user_email": user.get("email"),
        "user_roles": user.get("roles", [])
    }


@router.get("/super-admin/protected")
async def super_admin_protected(user: dict = SUPER_ADMIN_ONLY):
    return {
        "message": "Welcome, Super Admin!",
        "user_email": user.get("email"),
        "user_roles": user.get("roles", [])
    }


@router.post("/super-admin/create-admin", status_code=status.HTTP_201_CREATED)
async def create_admin_user(
    email: str = Body(..., embed=True),
    user: dict = SUPER_ADMIN_ONLY
):
    if email in USERS_DB:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )

    new_user = {
        "id": f"user-{len(USERS_DB) + 1}",
        "email": email,
        "password": f"temp_{email.split('@')[0]}",
        "roles": ["ADMIN"],
        "full_name": email.split("@")[0]
    }

    USERS_DB[email] = new_user

    return {
        "message": "Admin user created successfully",
        "user": {
            "id": new_user["id"],
            "email": new_user["email"],
            "roles": new_user["roles"]
        }
    }