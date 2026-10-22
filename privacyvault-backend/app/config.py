from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "PrivacyVault"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    API_PREFIX: str = "/api/v1"
    DATABASE_URL: str = "sqlite+aiosqlite:///./privacyvault.db"
    ENCRYPTION_SCHEME: str = "CKKS"
    POLY_MOD_DEGREE: int = 4096
    SCALE: int = 2**40
    CORS_ORIGINS: list = ["http://localhost:5173", "http://localhost:3000"]
    
    class Config:
        env_file = ".env"

settings = Settings()
