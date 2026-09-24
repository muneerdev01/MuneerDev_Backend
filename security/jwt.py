"""
JWT Authentication Utilities
"""
import secrets
import time
import hashlib
import base64
import hmac
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

from security.environment import get_required_env


# Get JWT secret from environment
JWT_SECRET = get_required_env("JWT_SECRET", "Secret key for token generation")
JWT_ALGORITHM = get_required_env("JWT_ALGORITHM", "Algorithm for token signing")
TOKEN_EXPIRY_HOURS = int(get_required_env("TOKEN_EXPIRY_HOURS", "Token expiry in hours"))


def base64url_encode(data: bytes) -> str:
    """Encode bytes to base64url format"""
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')


def base64url_decode(data: str) -> bytes:
    """Decode base64url format to bytes"""
    # Add padding if needed
    padding = 4 - len(data) % 4
    if padding != 4:
        data += '=' * padding
    return base64.urlsafe_b64decode(data)


def create_jwt_token(
    user_id: str,
    email: str,
    roles: List[str],
    additional_claims: Dict[str, Any] = None
) -> str:
    """
    Create a JWT token for authentication.
    
    Args:
        user_id: User's unique identifier
        email: User's email address
        roles: List of user roles (SUPER_ADMIN, ADMIN, EDITOR)
        additional_claims: Optional additional claims to include
        
    Returns:
        Signed JWT token string
    """
    # Token header
    header = {
        "alg": JWT_ALGORITHM,
        "typ": "JWT"
    }
    
    # Token payload
    now = datetime.utcnow()
    payload = {
        "sub": user_id,  # Subject
        "email": email,
        "roles": roles,
        "iat": now.timestamp(),  # Issued at
        "exp": (now + timedelta(hours=TOKEN_EXPIRY_HOURS)).timestamp(),  # Expiration
        "jti": base64url_encode(secrets.token_bytes(16)),  # JWT ID for revocation
    }
    
    # Add additional claims
    if additional_claims:
        payload.update(additional_claims)
    
    # Encode header and payload
    header_b64 = base64url_encode(json.dumps(header).encode('utf-8'))
    payload_b64 = base64url_encode(json.dumps(payload).encode('utf-8'))
    
    # Create signature
    message = f"{header_b64}.{payload_b64}"
    signature = hmac.new(
        JWT_SECRET.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).digest()
    signature_b64 = base64url_encode(signature)
    
    return f"{message}.{signature_b64}"


def verify_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded payload if valid, None if invalid
    """
    try:
        # Split token
        parts = token.split('.')
        if len(parts) != 3:
            return None
        
        header_b64, payload_b64, signature_b64 = parts
        
        # Verify signature
        message = f"{header_b64}.{payload_b64}"
        expected_signature = hmac.new(
            JWT_SECRET.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).digest()
        expected_signature_b64 = base64url_encode(expected_signature)
        
        if not hmac.compare_digest(signature_b64, expected_signature_b64):
            return None
        
        # Decode payload
        payload_bytes = base64url_decode(payload_b64)
        payload = json.loads(payload_bytes)
        
        # Check expiration
        if payload.get("exp", 0) < time.time():
            return None
        
        # Check JWT ID wasn't revoked (in production, check against DB)
        # For now, just validate structure
        
        return payload
        
    except Exception:
        return None


def decode_token_without_verification(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode token payload without verification (for logging/debugging).
    NEVER use this for authentication decisions.
    """
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        
        payload_b64 = parts[1]
        payload_bytes = base64url_decode(payload_b64)
        return json.loads(payload_bytes)
    except Exception:
        return None


def get_current_user_from_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Get current user info from token.
    
    Returns user data if token is valid and not expired.
    """
    return verify_jwt_token(token)


def has_role(roles: List[str], required_role: str) -> bool:
    """
    Check if user has required role.
    
    Args:
        roles: User's roles
        required_role: Role to check for
        
    Returns:
        True if user has the role
    """
    return required_role in roles


def require_roles(roles: List[str], required_roles: List[str]) -> bool:
    """
    Check if user has all required roles.
    
    Args:
        roles: User's roles
        required_roles: Roles to check for
        
    Returns:
        True if user has all required roles
    """
    return all(role in roles for role in required_roles)
