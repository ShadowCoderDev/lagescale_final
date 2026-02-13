import logging
import threading
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.core.config import settings
from app.api import notifications
from app.services.rabbitmq_consumer import notification_consumer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

consumer_thread = None


def start_consumer():
    try:
        notification_consumer.start_consuming()
    except Exception as e:
        logger.error(f"Consumer error: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global consumer_thread
    
    logger.info(f"Starting {settings.SERVICE_NAME} v{settings.VERSION}")
    
    consumer_thread = threading.Thread(target=start_consumer, daemon=True)
    consumer_thread.start()
    logger.info("RabbitMQ consumer started in background")
    
    yield
    
    logger.info(f"Shutting down {settings.SERVICE_NAME}")
    notification_consumer.disconnect()


app = FastAPI(
    title="Notification Service API",
    version=settings.VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(notifications.router)

Instrumentator().instrument(app).expose(app)


@app.get("/health", tags=["Health"])
async def health_check():
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
