"""
Application Settings
Configuration loaded from environment variables with FAIL-SECURE validation
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from typing import Optional

# Load .env file explicitly
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=False)


class Settings(BaseSettings):
    """Application settings"""
    
    # App Settings
    APP_NAME: str = "MuneerDev Blog"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # Database Settings
    DATABASE_URL: str = ""
    
    # JWT Settings (FAIL-SECURE: required)
    JWT_SECRET: str = ""
    JWT_ALGORITHM: str = "HS256"
    TOKEN_EXPIRY_HOURS: int = 24
    
    # Supabase Settings
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_KEY: str = ""
    
    # Admin Configuration (FAIL-SECURE: required)
    ADMIN_EMAIL: str = ""
    ADMIN_SECRET_KEY: str = ""
    
    # CORS Settings
    NEXT_PUBLIC_APP_URL: str = "http://localhost:3000"
    APP_URL: str = "https://muneerdev.com"
    
    # Author / Site Owner Configuration
    SITE_AUTHOR: str = "Muneer"
    SITE_AUTHOR_EMAIL: str = "muneer.dev01@gmail.com"
    SITE_AUTHOR_WHATSAPP: str = "+923151304012"
    PRIMARY_DOMAIN: str = "https://muneerdev.com"
    
    # Article Settings
    DEFAULT_READING_SPEED: int = 200  # words per minute
    DEFAULT_PAGE_SIZE: int = 10
    MAX_PAGE_SIZE: int = 100
    
    # Storage Settings
    STORAGE_BUCKET: str = "media"
    DEFAULT_FILE_PATH: str = "uploads"
    
    # Healthcare Settings
    MANDATORY_DISCLAIMER: str = """**DISCLAIMER:** This content is for informational purposes only and is not intended as medical advice, diagnosis, or treatment. Always seek the advice of your physician or other qualified health provider with any questions you may have regarding a medical condition. Never disregard professional medical advice or delay seeking care based on information contained in this article."""
    
    # Healthcare Author Configuration
    HEALTHCARE_AUTHOR_NAME: str = "Muneer"
    HEALTHCARE_AUTHOR_EMAIL: str = "muneer.dev01@gmail.com"
    HEALTHCARE_AUTHOR_CREDENTIALS: str = "Healthcare Content Reviewer"
    HEALTHCARE_CONTACT_WHATSAPP: str = "+923151304012"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance - validation happens on import
settings = Settings()