import os


class Settings:
    SERVICE_NAME: str = "notification-service"
    VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8005"))
    
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./notifications.db")
    
    RABBITMQ_HOST: str = os.getenv("RABBITMQ_HOST", "localhost")
    RABBITMQ_PORT: int = int(os.getenv("RABBITMQ_PORT", "5672"))
    RABBITMQ_USER: str = os.getenv("RABBITMQ_USER", "guest")
    RABBITMQ_PASSWORD: str = os.getenv("RABBITMQ_PASSWORD", "guest")
    RABBITMQ_VHOST: str = os.getenv("RABBITMQ_VHOST", "/")
    
    EXCHANGE_NAME: str = os.getenv("EXCHANGE_NAME", "ecommerce")
    NOTIFICATION_QUEUE: str = os.getenv("NOTIFICATION_QUEUE", "notifications")
    ORDER_QUEUE: str = os.getenv("ORDER_QUEUE", "order_notifications")
    
    SMTP_HOST: str = os.getenv("SMTP_HOST", "localhost")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", "noreply@ecommerce.local")
    EMAIL_FROM_NAME: str = os.getenv("EMAIL_FROM_NAME", "E-Commerce Store")
    SMTP_USE_TLS: bool = os.getenv("SMTP_USE_TLS", "true").lower() == "true"


settings = Settings()

