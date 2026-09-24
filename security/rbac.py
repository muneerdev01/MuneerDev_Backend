"""
Role-Based Access Control (RBAC)
Server-side role validation and decorators
"""
from typing import List, Callable, Any, Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from security.jwt import verify_jwt_token, decode_token_without_verification

# Security scheme for Bearer tokens
security = HTTPBearer(auto_error=False)

# Role hierarchy: SUPER_ADMIN > ADMIN > EDITOR
ROLE_HIERARCHY = {
    "SUPER_ADMIN": 3,
    "ADMIN": 2,
    "EDITOR": 1
}


def get_role_level(role: str) -> int:
    """Get numeric level for a role"""
    return ROLE_HIERARCHY.get(role, 0)


def has_permission(user_roles: List[str], required_role: str) -> bool:
    """
    Check if user has required role or higher.
    
    Args:
        user_roles: User's roles
        required_role: Minimum required role
        
    Returns:
        True if user has sufficient permissions
    """
    user_level = max(get_role_level(role) for role in user_roles) if user_roles else 0
    required_level = get_role_level(required_role)
    return user_level >= required_level


class RBACChecker:
    """
    RBAC dependency for FastAPI routes.
    Enforces server-side role checks.
    """
    
    def __init__(self, required_roles: List[str]):
        """
        Initialize checker with required roles.
        
        Args:
            required_roles: List of roles that can access the endpoint.
                           Any role in the list grants access.
        """
        self.required_roles = required_roles
    
    def __call__(self, credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
        """
        Validate token and check roles.
        
        Raises:
            HTTPException: If authentication or authorization fails
        """
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Verify token
        payload = verify_jwt_token(credentials.credentials)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Get user roles
        user_roles = payload.get("roles", [])
        
        # Check if user has any required role
        has_access = any(
            has_permission(user_roles, role)
            for role in self.required_roles
        )
        
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {self.required_roles}"
            )
        
        return payload


def require_role(required_role: str):
    """
    Decorator for FastAPI endpoints requiring a specific role.
    
    Usage:
        @app.get("/admin")
        async def admin_endpoint(user: dict = Depends(require_role("ADMIN"))):
            return {"message": "Welcome, admin!"}
    """
    async def check_role(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Verify token
        payload = verify_jwt_token(credentials.credentials)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Get user roles
        user_roles = payload.get("roles", [])
        
        # Check if user has the required role
        if not any(has_permission(user_roles, role) for role in [required_role]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {required_role}"
            )
        
        return payload
    
    return check_role


def require_any_role(roles: List[str]):
    """
    Decorator for endpoints requiring any of multiple roles.
    
    Usage:
        @app.get("/write")
        async def write_endpoint(user: dict = Depends(require_any_role(["ADMIN", "EDITOR"]))):
            return {"message": "You can write content"}
    """
    async def check_roles(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Verify token
        payload = verify_jwt_token(credentials.credentials)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Get user roles
        user_roles = payload.get("roles", [])
        
        # Check if user has any required role
        has_access = any(
            has_permission(user_roles, role)
            for role in roles
        )
        
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {roles}"
            )
        
        return payload
    
    return check_roles


def require_all_roles(roles: List[str]):
    """
    Decorator for endpoints requiring ALL specified roles.
    
    Usage:
        @app.get("/super")
        async def super_endpoint(user: dict = Depends(require_all_roles(["ADMIN", "MANAGER"]))):
            return {"message": "Super access granted"}
    """
    def checker(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
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
        
        user_roles = payload.get("roles", [])
        
        # Check if user has ALL required roles
        missing_roles = [role for role in roles if role not in user_roles]
        if missing_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required roles: {missing_roles}"
            )
        
        return payload
    
    return Depends(checker)


# Convenience constants
SUPER_ADMIN_ONLY = require_role("SUPER_ADMIN")
ADMIN_ONLY = require_role("ADMIN")
EDITOR_ONLY = require_role("EDITOR")
ADMIN_OR_EDITOR = require_any_role(["ADMIN", "EDITOR"])
ANY_ROLE = require_any_role(["SUPER_ADMIN", "ADMIN", "EDITOR"])
