"""Pytest configuration and fixtures"""
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from bson import ObjectId

from app.main import app


# Mock product data
MOCK_PRODUCT = {
    "_id": ObjectId("507f1f77bcf86cd799439011"),
    "name": "Test Product",
    "description": "Test description",
    "price": 99.99,
    "stockQuantity": 10,
    "category": "Electronics",
    "sku": "TEST-001",
    "isActive": True,
    "createdAt": datetime.utcnow(),
    "updatedAt": datetime.utcnow(),
}


@pytest.fixture
def mock_db():
    """Create mock database"""
    mock = MagicMock()
    mock.products = MagicMock()
    return mock


@pytest.fixture
def admin_token():
    """Create admin JWT token"""
    from jose import jwt
    from app.core.config import settings
    
    payload = {
        "user_id": 1,
        "is_admin": True,
        "type": "access"
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


@pytest.fixture
def user_token():
    """Create regular user JWT token"""
    from jose import jwt
    from app.core.config import settings
    
    payload = {
        "user_id": 2,
        "is_admin": False,
        "type": "access"
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


@pytest.fixture
async def client(mock_db):
    """Create test client with mocked database"""
    with patch("app.api.products.get_database", return_value=mock_db):
        with patch("app.core.database.connect_to_mongo", new_callable=AsyncMock):
            with patch("app.core.database.close_mongo_connection", new_callable=AsyncMock):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as ac:
                    yield ac
