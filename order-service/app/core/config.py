"""Configuration settings"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings"""
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/orderdb"
    
    # JWT (for verifying tokens from user-service)
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    
    # External Services
    PRODUCT_SERVICE_URL: str = "http://localhost:8002"
    PAYMENT_SERVICE_URL: str = "http://localhost:8004"
    USER_SERVICE_URL: str = "http://localhost:8001"
    
    # RabbitMQ (for notifications)
    RABBITMQ_HOST: str = "localhost"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = "guest"
    RABBITMQ_PASSWORD: str = "guest"
    RABBITMQ_VHOST: str = "/"
    NOTIFICATION_QUEUE: str = "order_notifications"
    STOCK_QUEUE: str = "stock_updates"
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    class Config:
        env_file = ".env"


settings = Settings()
