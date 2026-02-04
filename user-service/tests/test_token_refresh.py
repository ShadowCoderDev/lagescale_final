"""
Tests for token refresh endpoint
"""
import pytest
from fastapi import status
from app.core.security import create_refresh_token, create_access_token


class TestTokenRefresh:
    """Test cases for token refresh endpoint"""
    
    def test_refresh_token_success(self, client, test_user):
        """Test successful token refresh"""
        # First login to set cookies
        login_data = {
            "email": "test@example.com",
            "password": "testpass123"
        }
        login_response = client.post("/api/users/login/", json=login_data)
        assert login_response.status_code == status.HTTP_200_OK
        
        # Now refresh token using cookies
        response = client.post("/api/users/token/refresh/")
        
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert "message" in response_data
        assert "refreshed" in response_data["message"].lower()
        
        # Check new access token cookie is set
        assert "access_token" in response.cookies
    
    def test_refresh_token_no_cookie(self, client):
        """Test token refresh without refresh token cookie"""
        response = client.post("/api/users/token/refresh/")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "not found" in response.json()["detail"].lower()
    
    def test_refresh_token_invalid_token(self, client):
        """Test token refresh with invalid refresh token"""
        # Set invalid refresh token cookie manually
        client.cookies.set("refresh_token", "invalid_token")
        
        response = client.post("/api/users/token/refresh/")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_refresh_token_wrong_type(self, client, test_user):
        """Test token refresh with access token instead of refresh token"""
        # Create access token and use it as refresh token
        access_token = create_access_token({
            "user_id": test_user.id,
            "is_admin": test_user.is_admin
        })
        client.cookies.set("refresh_token", access_token)
        
        response = client.post("/api/users/token/refresh/")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "token type" in response.json()["detail"].lower()
    
    def test_refresh_token_user_not_found(self, client, db):
        """Test token refresh for deleted user"""
        # Create refresh token for non-existent user
        refresh_token = create_refresh_token({
            "user_id": 99999,
            "is_admin": False
        })
        client.cookies.set("refresh_token", refresh_token)
        
        response = client.post("/api/users/token/refresh/")
        
        # User not found can return 401 or 404
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_404_NOT_FOUND]
    
    def test_refresh_token_inactive_user(self, client, db):
        """Test token refresh for inactive user"""
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
        
        # Create refresh token for inactive user
        refresh_token = create_refresh_token({
            "user_id": user.id,
            "is_admin": False
        })
        client.cookies.set("refresh_token", refresh_token)
        
        response = client.post("/api/users/token/refresh/")
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        # Support both English and Persian messages
        detail = response.json()["detail"].lower()
        assert "disabled" in detail or "غیرفعال" in detail
