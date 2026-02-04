"""Test configuration"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
from decimal import Decimal
from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from jose import jwt

from app.main import app
from app.core.database import Base, get_db
from app.core.config import settings
from app.models.order import Order, OrderItem, OrderStatus

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_orders.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
def db():
    """Create test database"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
async def client(db):
    """Test client"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
def user_token():
    """Generate user token"""
    payload = {
        "user_id": 1,
        "is_admin": False,
        "exp": datetime.utcnow() + timedelta(hours=1),
        "type": "access"
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


@pytest.fixture
def mock_product():
    """Mock product data"""
    return {
        "id": "507f1f77bcf86cd799439011",
        "name": "Test Product",
        "price": 99.99,
        "stockQuantity": 10,
        "isActive": True
    }


@pytest.fixture
def sample_order(db):
    """Create sample order"""
    order = Order(
        user_id=1,
        total_amount=Decimal("99.99"),
        status=OrderStatus.PENDING,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(order)
    db.flush()
    
    item = OrderItem(
        order_id=order.id,
        product_id="507f1f77bcf86cd799439011",
        product_name="Test Product",
        quantity=1,
        unit_price=Decimal("99.99"),
        subtotal=Decimal("99.99"),
        created_at=datetime.utcnow()
    )
    db.add(item)
    db.commit()
    db.refresh(order)
    
    return order
