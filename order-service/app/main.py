"""FastAPI application"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from app.core.config import settings
from app.api import orders

app = FastAPI(
    title="Order Service",
    description="Order management service",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(orders.router, prefix="/api/orders", tags=["Orders"])

# Prometheus metrics - exposes /metrics endpoint
Instrumentator().instrument(app).expose(app)


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "order-service"}
