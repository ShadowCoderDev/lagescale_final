"""Notification Service - Main Application"""
import logging
import threading
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.core.config import settings
from app.api import notifications
from app.services.rabbitmq_consumer import notification_consumer
from app.db.base import init_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Consumer thread
consumer_thread = None


def start_consumer():
    """Start RabbitMQ consumer in background"""
    try:
        notification_consumer.start_consuming()
    except Exception as e:
        logger.error(f"Consumer error: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events"""
    global consumer_thread
    
    # Startup
    logger.info(f"Starting {settings.SERVICE_NAME} v{settings.VERSION}")
    
    # Initialize database tables
    init_db()
    logger.info("Database initialized")
    
    # Start RabbitMQ consumer in background thread
    consumer_thread = threading.Thread(target=start_consumer, daemon=True)
    consumer_thread.start()
    logger.info("RabbitMQ consumer started in background")
    
    yield
    
    # Shutdown
    logger.info(f"Shutting down {settings.SERVICE_NAME}")
    notification_consumer.disconnect()


# Create FastAPI app
app = FastAPI(
    title="Notification Service API",
    description="""
    Notification Service for e-commerce platform.
    
    This service listens to RabbitMQ for order events and sends email notifications.
    
    ## Events Handled
    
    - `order_created` - Order placed by customer
    - `payment_success` - Payment processed successfully
    - `payment_failed` - Payment failed
    - `order_canceled` - Order canceled
    
    ## Architecture
    
    ```
    Order Service → RabbitMQ → Notification Service → SMTP → Email
    ```
    """,
    version=settings.VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(notifications.router)

# Prometheus metrics - exposes /metrics endpoint
Instrumentator().instrument(app).expose(app)


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "version": settings.VERSION
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
