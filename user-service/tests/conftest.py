"""
Pytest configuration and fixtures
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import Base, get_db
from app.models.user import User

# Test database URL (SQLite in-memory for testing)
TEST_DATABASE_URL = "sqlite:///./test.db"

# Create test engine
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """
    Create a fresh database for each test
    """
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Drop tables after test
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    """
    Create a test client with database override
    """
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db):
    """
    Create a test user in database
    """
    from app.core.security import hash_password
    
    user = User(
        email="test@example.com",
        hashed_password=hash_password("testpass123"),
        first_name="Test",
        last_name="User",
        is_active=True,
        is_admin=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_admin_user(db):
    """
    Create a test admin user in database
    """
    from app.core.security import hash_password
    
    user = User(
        email="admin@example.com",
        hashed_password=hash_password("adminpass123"),
        first_name="Admin",
        last_name="User",
        is_active=True,
        is_admin=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user):
    """
    Create authentication headers for test user
    """
    from app.core.security import create_token_pair
    
    tokens = create_token_pair(test_user.id, test_user.is_admin)
    return {"Authorization": f"Bearer {tokens['access']}"}


@pytest.fixture
def admin_auth_headers(test_admin_user):
    """
    Create authentication headers for admin user
    """
    from app.core.security import create_token_pair
    
    tokens = create_token_pair(test_admin_user.id, test_admin_user.is_admin)
    return {"Authorization": f"Bearer {tokens['access']}"}
