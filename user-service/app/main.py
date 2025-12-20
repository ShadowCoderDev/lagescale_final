"""
Main FastAPI Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import users

app = FastAPI(
    title="User Service API",
    description="User authentication and profile management service",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(users.router, prefix="/api/users", tags=["users"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "User Service API is running"}


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}
