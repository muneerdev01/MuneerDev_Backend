"""
Authentication & Authorization Schemas
"""
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field


class Token(BaseModel):
    """Access token response"""
    access_token: str
    token_type: str = "Bearer"
    expires_in: int


class TokenPayload(BaseModel):
    """Token payload structure"""
    sub: str
    email: str
    roles: List[str] = Field(default_factory=list)
    iat: float
    exp: float
    jti: str


class LoginRequest(BaseModel):
    """Login request payload"""
    email: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=1, max_length=128)


class LoginResponse(BaseModel):
    """Login response with token"""
    token: Token
    user: Dict[str, Any]


class RefreshRequest(BaseModel):
    """Token refresh request"""
    refresh_token: str


class RefreshResponse(BaseModel):
    """Refresh response with new token"""
    access_token: str
    token_type: str = "Bearer"
    expires_in: int


class RegisterRequest(BaseModel):
    """Registration request payload"""
    email: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    full_name: Optional[str] = Field(default=None, max_length=255)


class RegisterResponse(BaseModel):
    """Registration response"""
    message: str
    user: Dict[str, Any]


class ChangePasswordRequest(BaseModel):
    """Change password request"""
    current_password: str = Field(..., min_length=8, max_length=128)
    new_password: str = Field(..., min_length=8, max_length=128)


class ForgotPasswordRequest(BaseModel):
    """Forgot password request"""
    email: str = Field(..., min_length=1, max_length=255)


class ResetPasswordRequest(BaseModel):
    """Reset password request"""
    token: str = Field(...)
    new_password: str = Field(..., min_length=8, max_length=128)
