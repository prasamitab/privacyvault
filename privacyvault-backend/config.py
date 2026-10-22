"""
Configuration settings for PrivacyVault backend
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    
    # App settings
    APP_NAME: str = "PrivacyVault"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # API settings
    API_PREFIX: str = "/api/v1"
    
    # Database settings
    DATABASE_URL: str = "sqlite+aiosqlite:///./privacyvault.db"
    
    # Encryption settings
    ENCRYPTION_SCHEME: str = "CKKS"  # CKKS for approximate numbers (salaries)
    POLY_MOD_DEGREE: int = 4096  # Polynomial modulus degree
    SCALE: int = 2**40  # Scaling factor for CKKS
    
    # Security settings
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS settings
    CORS_ORIGINS: list = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()