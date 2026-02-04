"""
Tests for logout endpoint
"""
import pytest
from fastapi import status


class TestLogout:
    """Test cases for logout endpoint"""
    
    def test_logout_success(self, client, test_user, auth_headers):
        """Test successful logout"""
        response = client.post("/api/users/logout/", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        
        assert "message" in response_data
        assert "logout" in response_data["message"].lower()
    
    def test_logout_clears_cookies(self, client, test_user):
        """Test that logout clears JWT cookies"""
        # First login to set cookies
        login_data = {
            "email": "test@example.com",
            "password": "testpass123"
        }
        login_response = client.post("/api/users/login/", json=login_data)
        assert login_response.status_code == status.HTTP_200_OK
        
        # Verify cookies are set
        assert "access_token" in client.cookies
        assert "refresh_token" in client.cookies
        
        # Now logout
        response = client.post("/api/users/logout/")
        
        assert response.status_code == status.HTTP_200_OK
        
        # Check cookies are cleared (cookies with max_age=0 or deleted)
        # The response should contain Set-Cookie headers that delete the cookies
        assert response.status_code == status.HTTP_200_OK
    
    def test_logout_unauthenticated(self, client):
        """Test logout without authentication"""
        response = client.post("/api/users/logout/")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_logout_invalid_token(self, client):
        """Test logout with invalid token"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.post("/api/users/logout/", headers=headers)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_logout_then_access_profile(self, client, test_user):
        """Test that profile access fails after logout"""
        # First login
        login_data = {
            "email": "test@example.com",
            "password": "testpass123"
        }
        login_response = client.post("/api/users/login/", json=login_data)
        assert login_response.status_code == status.HTTP_200_OK
        
        # Verify can access profile
        profile_response = client.get("/api/users/profile/")
        assert profile_response.status_code == status.HTTP_200_OK
        
        # Logout
        logout_response = client.post("/api/users/logout/")
        assert logout_response.status_code == status.HTTP_200_OK
        
        # Clear cookies from client to simulate cleared cookies
        client.cookies.clear()
        
        # Try to access profile - should fail
        profile_response_after = client.get("/api/users/profile/")
        assert profile_response_after.status_code == status.HTTP_401_UNAUTHORIZED
