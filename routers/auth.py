"""
Authentication Router
JWT-based authentication for Admin endpoints
"""
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

# Hardcoded users for demo (replace with database lookup in production)
USERS_DB = {
    "superadmin@example.com": {
        "id": "super-admin-uuid",
        "email": "superadmin@example.com",
        "password": "superadmin123",
        "roles": ["SUPER_ADMIN"],
        "full_name": "Super Admin"
    },
    "admin@example.com": {
        "id": "admin-uuid",
        "email": "admin@example.com",
        "password": "admin123",
        "roles": ["ADMIN"],
        "full_name": "Admin User"
    },
    "editor@example.com": {
        "id": "editor-uuid",
        "email": "editor@example.com",
        "password": "editor123",
        "roles": ["EDITOR"],
        "full_name": "Editor User"
    }
}


def authenticate_user(email: str, password: str) -> dict:
    """
    Authenticate user against hardcoded database.
    Replace with database lookup in production.
    
    Args:
        email: User's email
        password: User's password
        
    Returns:
        User data if authenticated, None otherwise
    """
    user = USERS_DB.get(email)
    if not user:
        return None
    
    if user["password"] != password:
        return None
    
    return user


def create_access_token(user: dict) -> Token:
    """
    Create access token for authenticated user.
    
    Args:
        user: User data dict
        
    Returns:
        Token with JWT
    """
    jwt_token = create_jwt_token(
        user_id=user["id"],
        email=user["email"],
        roles=user["roles"]
    )
    
    return Token(access_token=jwt_token, token_type="Bearer", expires_in=86400)  # 24 hours


@router.post("/login", response_model=LoginResponse)
async def login(
    credentials: LoginRequest,
    db=Depends(get_db)
):
    """
    Login endpoint for authentication.
    
    Args:
        credentials: Email and password
        
    Returns:
        Access token and user info
    """
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
            "full_name": user.get("full_name")
        }
    )


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest
):
    """
    Register a new user.
    In production, this would save to database and send verification email.
    """
    if request.email in USERS_DB:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    new_user = {
        "id": f"user-{len(USERS_DB) + 1}",
        "email": request.email,
        "password": request.password,
        "roles": ["EDITOR"],  # Default role for new users
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


# Protected endpoints
@router.get("/admin/protected")
async def admin_protected(user: dict = ADMIN_ONLY):
    """
    Admin-only endpoint.
    """
    return {
        "message": "Welcome, Admin!",
        "user_email": user.get("email"),
        "user_roles": user.get("roles", [])
    }


@router.get("/editor/protected")
async def editor_protected(user: dict = ADMIN_OR_EDITOR):
    """
    Admin or Editor endpoint.
    """
    return {
        "message": "Welcome, Admin or Editor!",
        "user_email": user.get("email"),
        "user_roles": user.get("roles", [])
    }


@router.get("/super-admin/protected")
async def super_admin_protected(user: dict = SUPER_ADMIN_ONLY):
    """
    Super Admin-only endpoint.
    """
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
    """
    Create a new admin user (Super Admin only).
    """
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
