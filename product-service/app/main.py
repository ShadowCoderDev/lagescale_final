"""Main FastAPI Application"""
import logging
import threading
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from prometheus_fastapi_instrumentator import Instrumentator

from app.core.config import settings
from app.core.database import connect_to_mongo, close_mongo_connection
from app.api import products
from app.services.stock_consumer import stock_consumer

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
        stock_consumer.start_consuming()
    except Exception as e:
        logger.error(f"Stock consumer error: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    global consumer_thread
    
    await connect_to_mongo()
    logger.info("Product Service started")
    
    # Start RabbitMQ consumer in background thread
    consumer_thread = threading.Thread(target=start_consumer, daemon=True)
    consumer_thread.start()
    logger.info("Stock consumer started in background")
    
    yield
    
    await close_mongo_connection()
    stock_consumer.disconnect()
    logger.info("Product Service stopped")


app = FastAPI(
    title="Product Service API",
    description="Product management service",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(products.router, prefix="/api/products", tags=["products"])

# Prometheus metrics - exposes /metrics endpoint
Instrumentator().instrument(app).expose(app)


@app.get("/")
async def root():
    return {"message": "Product Service API"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
