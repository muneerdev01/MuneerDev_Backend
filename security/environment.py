"""
Environment Validation - FAIL-SECURE Setup
Validates required environment variables on startup
"""
import os
import sys


def validate_environment() -> dict:
    """
    Validate all required environment variables.
    Throws RuntimeError if any critical variables are missing.
    
    FAIL-SECURE POLICY:
    - No hardcoded fallbacks for secrets
    - No default passwords
    - Missing variables = startup failure
    
    Returns:
        dict of validated environment variables
    """
    # Critical security variables (MUST be set)
    critical_vars = {
        "JWT_SECRET": "JWT secret key for token generation (minimum 32 chars)",
        "DATABASE_URL": "Database connection string (Supabase PostgreSQL)",
        "ADMIN_EMAIL": "Primary admin email address",
        "ADMIN_SECRET_KEY": "Admin authentication secret key",
    }
    
    validated = {}
    missing = []
    
    for var_name, description in critical_vars.items():
        value = os.getenv(var_name)
        
        if not value:
            missing.append((var_name, description))
        else:
            validated[var_name] = value
    
    # Set defaults for non-critical variables
    if not os.getenv("JWT_ALGORITHM"):
        os.environ["JWT_ALGORITHM"] = "HS256"
    if not os.getenv("TOKEN_EXPIRY_HOURS"):
        os.environ["TOKEN_EXPIRY_HOURS"] = "24"
    
    # FAIL-SECURE: Abort if critical variables missing
    if missing:
        error_msg = [
            "\n" + "=" * 60,
            "❌ FAIL-SECURE VALIDATION FAILED",
            "=" * 60,
            "Missing required environment variables:",
            ""
        ]
        
        for var_name, description in missing:
            error_msg.append(f"  • {var_name}")
            error_msg.append(f"    {description}")
        
        error_msg.extend([
            "",
            "=" * 60,
            "SECURITY POLICY: Application cannot start without these values.",
            "=" * 60,
            "To fix, set these variables in your .env file:",
            f"  1. cp .env.example .env",
            "  2. Edit .env with your actual values",
            "",
            "Do NOT use hardcoded fallbacks in production!",
            "=" * 60
        ])
        
        print("\n".join(error_msg))
        sys.exit(1)
    
    # Validate JWT_SECRET strength
    jwt_secret = validated.get("JWT_SECRET", "")
    if len(jwt_secret) < 32:
        print("\n" + "=" * 60)
        print("❌ JWT_SECRET must be at least 32 characters long for security")
        print("=" * 60)
        sys.exit(1)
    
    print("✅ FAIL-SECURE Environment validation passed")
    return validated


def get_required_env(var_name: str, description: str = "") -> str:
    """
    Get a required environment variable or raise error.
    
    Args:
        var_name: Environment variable name
        description: Variable description for error message
        
    Returns:
        Value of the environment variable
    """
    value = os.getenv(var_name)
    
    if not value:
        print("\n" + "=" * 60)
        print(f"❌ Missing required environment variable: {var_name}")
        if description:
            print(f"   {description}")
        print("=" * 60)
        sys.exit(1)
    
    return value