from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/userdb"
    
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 4320  # 3 days
    REFRESH_TOKEN_EXPIRE_DAYS: int = 14
    
    ACCESS_COOKIE_NAME: str = "access_token"
    REFRESH_COOKIE_NAME: str = "refresh_token"
    COOKIE_DOMAIN: Optional[str] = None
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: str = "lax"
    
    ALLOWED_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    class Config:
        env_file = ".env"


settings = Settings()
