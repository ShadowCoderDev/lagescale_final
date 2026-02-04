"""Test configuration"""
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import MagicMock, patch

from app.main import app


@pytest.fixture
async def client():
    """Async test client"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
def mock_smtp():
    """Mock SMTP server"""
    with patch("smtplib.SMTP") as mock:
        yield mock


@pytest.fixture
def sample_order_created_data():
    """Sample order created event data"""
    return {
        "email": "test@example.com",
        "order_id": 123,
        "total_amount": 99.99
    }


@pytest.fixture
def sample_payment_success_data():
    """Sample payment success event data"""
    return {
        "email": "test@example.com",
        "order_id": 123,
        "transaction_id": "txn-abc-123"
    }


@pytest.fixture
def sample_payment_failed_data():
    """Sample payment failed event data"""
    return {
        "email": "test@example.com",
        "order_id": 123,
        "reason": "Card declined"
    }


@pytest.fixture
def sample_order_canceled_data():
    """Sample order canceled event data"""
    return {
        "email": "test@example.com",
        "order_id": 123
    }
