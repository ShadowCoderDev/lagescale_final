"""Configuration settings"""
from pydantic_settings import BaseSettings
from pydantic import computed_field
from typing import List, Optional


class Settings(BaseSettings):
    """Application settings"""
    
    # MongoDB - individual settings (for Kubernetes ConfigMap compatibility)
    MONGODB_HOST: str = "localhost"
    MONGODB_PORT: int = 27017
    MONGODB_USERNAME: Optional[str] = None
    MONGODB_PASSWORD: Optional[str] = None
    MONGODB_DATABASE: str = "products_db"
    MONGODB_URL: Optional[str] = None  # Can override the computed URL
    
    @computed_field
    @property
    def MONGODB_CONNECTION_URL(self) -> str:
        """Build MongoDB URL from individual settings or use MONGODB_URL if provided"""
        if self.MONGODB_URL:
            return self.MONGODB_URL
        if self.MONGODB_USERNAME and self.MONGODB_PASSWORD:
            return f"mongodb://{self.MONGODB_USERNAME}:{self.MONGODB_PASSWORD}@{self.MONGODB_HOST}:{self.MONGODB_PORT}/{self.MONGODB_DATABASE}?authSource=admin"
        return f"mongodb://{self.MONGODB_HOST}:{self.MONGODB_PORT}/{self.MONGODB_DATABASE}"
    
    MONGODB_DB_NAME: str = "products_db"  # Kept for backward compatibility
    
    # JWT (for verifying tokens from user-service)
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    
    # RabbitMQ - using RMQ_ prefix to avoid Kubernetes service variable collision
    RMQ_HOST: str = "localhost"
    RMQ_PORT: int = 5672
    RMQ_USER: str = "guest"
    RMQ_PASSWORD: str = "guest"
    RMQ_VHOST: str = "/"
    STOCK_QUEUE: str = "stock_updates"
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    class Config:
        env_file = ".env"


settings = Settings()
