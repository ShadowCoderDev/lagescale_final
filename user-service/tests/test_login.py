"""
Tests for user login endpoint
"""
import pytest
from fastapi import status


class TestUserLogin:
    """Test cases for user login"""
    
    def test_login_success(self, client, test_user):
        """Test successful user login"""
        data = {
            "email": "test@example.com",
            "password": "testpass123"
        }
        
        response = client.post("/api/users/login/", json=data)
        
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        
        assert "user" in response_data
        assert "tokens" in response_data
        assert "message" in response_data
        
        assert response_data["user"]["email"] == "test@example.com"
        assert response_data["user"]["first_name"] == "Test"
        assert response_data["user"]["last_name"] == "User"
        
        # Check tokens
        assert "access" in response_data["tokens"]
        assert "refresh" in response_data["tokens"]
        
        # Check cookies are set
        assert "access_token" in response.cookies
        assert "refresh_token" in response.cookies
    
    def test_login_wrong_password(self, client, test_user):
        """Test login with wrong password"""
        data = {
            "email": "test@example.com",
            "password": "wrongpassword"
        }
        
        response = client.post("/api/users/login/", json=data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        # Support both English and Persian messages
        detail = response.json()["detail"]
        assert "Invalid email or password" in detail or "ایمیل یا رمز عبور اشتباه" in detail
    
    def test_login_user_not_found(self, client):
        """Test login with non-existent user"""
        data = {
            "email": "nonexistent@example.com",
            "password": "testpass123"
        }
        
        response = client.post("/api/users/login/", json=data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        # Support both English and Persian messages
        detail = response.json()["detail"]
        assert "Invalid email or password" in detail or "ایمیل یا رمز عبور اشتباه" in detail
    
    def test_login_invalid_email_format(self, client):
        """Test login with invalid email format"""
        data = {
            "email": "not-an-email",
            "password": "testpass123"
        }
        
        response = client.post("/api/users/login/", json=data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_login_missing_password(self, client):
        """Test login without password"""
        data = {
            "email": "test@example.com"
        }
        
        response = client.post("/api/users/login/", json=data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_login_missing_email(self, client):
        """Test login without email"""
        data = {
            "password": "testpass123"
        }
        
        response = client.post("/api/users/login/", json=data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_login_inactive_user(self, client, db):
        """Test login with inactive user"""
        from app.core.security import hash_password
        from app.models.user import User
        
        # Create inactive user
        user = User(
            email="inactive@example.com",
            hashed_password=hash_password("testpass123"),
            is_active=False
        )
        db.add(user)
        db.commit()
        
        data = {
            "email": "inactive@example.com",
            "password": "testpass123"
        }
        
        response = client.post("/api/users/login/", json=data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        # Support both English and Persian messages
        detail = response.json()["detail"]
        assert "disabled" in detail or "غیرفعال" in detail
    
    def test_login_updates_last_login(self, client, test_user, db):
        """Test that login updates last_login field"""
        # Check last_login is initially None
        assert test_user.last_login is None
        
        data = {
            "email": "test@example.com",
            "password": "testpass123"
        }
        
        response = client.post("/api/users/login/", json=data)
        
        assert response.status_code == status.HTTP_200_OK
        
        # Refresh user from database
        db.refresh(test_user)
        
        # Check last_login is updated
        assert test_user.last_login is not None
