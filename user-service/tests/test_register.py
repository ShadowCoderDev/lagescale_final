"""
Tests for user registration endpoint
"""
import pytest
from fastapi import status


class TestUserRegistration:
    """Test cases for user registration"""
    
    def test_register_success(self, client):
        """Test successful user registration"""
        data = {
            "email": "newuser@example.com",
            "password": "testpass123",
            "password2": "testpass123",
            "first_name": "New",
            "last_name": "User"
        }
        
        response = client.post("/api/users/register/", json=data)
        
        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        
        assert "user" in response_data
        assert "tokens" in response_data
        assert "message" in response_data
        
        assert response_data["user"]["email"] == "newuser@example.com"
        assert response_data["user"]["first_name"] == "New"
        assert response_data["user"]["last_name"] == "User"
        assert response_data["user"]["is_admin"] is False
        
        # Check tokens
        assert "access" in response_data["tokens"]
        assert "refresh" in response_data["tokens"]
        
        # Check cookies are set
        assert "access_token" in response.cookies
        assert "refresh_token" in response.cookies
    
    def test_register_minimal_data(self, client):
        """Test registration with minimal data (only email and password)"""
        data = {
            "email": "minimal@example.com",
            "password": "testpass123",
            "password2": "testpass123"
        }
        
        response = client.post("/api/users/register/", json=data)
        
        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        
        assert response_data["user"]["email"] == "minimal@example.com"
        assert response_data["user"]["first_name"] is None
        assert response_data["user"]["last_name"] is None
    
    def test_register_password_mismatch(self, client):
        """Test registration with mismatched passwords"""
        data = {
            "email": "test@example.com",
            "password": "testpass123",
            "password2": "differentpass",
            "first_name": "Test",
            "last_name": "User"
        }
        
        response = client.post("/api/users/register/", json=data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_register_duplicate_email(self, client, test_user):
        """Test registration with duplicate email"""
        data = {
            "email": test_user.email,  # Use existing user's email
            "password": "testpass123",
            "password2": "testpass123"
        }
        
        response = client.post("/api/users/register/", json=data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        # Support both English and Persian messages
        detail = response.json()["detail"]
        assert "already exists" in detail or "قبلاً ثبت" in detail
    
    def test_register_invalid_email(self, client):
        """Test registration with invalid email"""
        data = {
            "email": "not-an-email",
            "password": "testpass123",
            "password2": "testpass123"
        }
        
        response = client.post("/api/users/register/", json=data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_register_short_password(self, client):
        """Test registration with short password"""
        data = {
            "email": "test@example.com",
            "password": "123",
            "password2": "123"
        }
        
        response = client.post("/api/users/register/", json=data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_register_missing_password(self, client):
        """Test registration without password"""
        data = {
            "email": "test@example.com"
        }
        
        response = client.post("/api/users/register/", json=data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_register_missing_email(self, client):
        """Test registration without email"""
        data = {
            "password": "testpass123",
            "password2": "testpass123"
        }
        
        response = client.post("/api/users/register/", json=data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
