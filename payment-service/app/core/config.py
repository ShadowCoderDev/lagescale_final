"""Payment Service Configuration"""
import os


class Settings:
    """Application settings"""
    
    # Service info
    SERVICE_NAME: str = "payment-service"
    VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8004
    
    # Database -  vars
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "5435"))
    DB_NAME: str = os.getenv("DB_NAME", "payments")
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "postgres")
    
    # Payment success rate
    SUCCESS_RATE: float = float(os.getenv("SUCCESS_RATE", "0.8"))
    
    @property
    def database_url(self) -> str:
        """Get database URL"""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


settings = Settings()
