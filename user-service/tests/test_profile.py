"""
Tests for user profile endpoint
"""
import pytest
from fastapi import status


class TestUserProfile:
    """Test cases for user profile endpoints"""
    
    def test_get_profile_success(self, client, test_user, auth_headers):
        """Test successful profile retrieval"""
        response = client.get("/api/users/profile/", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        
        assert response_data["id"] == test_user.id
        assert response_data["email"] == "test@example.com"
        assert response_data["first_name"] == "Test"
        assert response_data["last_name"] == "User"
        assert response_data["full_name"] == "Test User"
        assert response_data["is_admin"] is False
    
    def test_get_profile_unauthenticated(self, client):
        """Test profile retrieval without authentication"""
        response = client.get("/api/users/profile/")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_profile_invalid_token(self, client):
        """Test profile retrieval with invalid token"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/users/profile/", headers=headers)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_profile_admin_user(self, client, test_admin_user, admin_auth_headers):
        """Test profile retrieval for admin user"""
        response = client.get("/api/users/profile/", headers=admin_auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        
        assert response_data["email"] == "admin@example.com"
        assert response_data["is_admin"] is True
    
    def test_update_profile_put_success(self, client, test_user, auth_headers):
        """Test successful profile update with PUT"""
        data = {
            "first_name": "Updated",
            "last_name": "Name"
        }
        
        response = client.put("/api/users/profile/", json=data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        
        assert response_data["first_name"] == "Updated"
        assert response_data["last_name"] == "Name"
        assert response_data["full_name"] == "Updated Name"
    
    def test_update_profile_patch_success(self, client, test_user, auth_headers):
        """Test successful profile partial update with PATCH"""
        data = {
            "first_name": "PatchedFirst"
        }
        
        response = client.patch("/api/users/profile/", json=data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        
        assert response_data["first_name"] == "PatchedFirst"
        assert response_data["last_name"] == "User"  # Original value preserved
    
    def test_update_profile_unauthenticated(self, client):
        """Test profile update without authentication"""
        data = {
            "first_name": "Updated"
        }
        
        response = client.put("/api/users/profile/", json=data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_update_profile_empty_name(self, client, auth_headers):
        """Test profile update with empty name"""
        data = {
            "first_name": "   "  # Empty after strip
        }
        
        response = client.put("/api/users/profile/", json=data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_get_profile_with_cookie_auth(self, client, test_user):
        """Test profile retrieval using cookie authentication"""
        # First login to get cookies
        login_data = {
            "email": "test@example.com",
            "password": "testpass123"
        }
        login_response = client.post("/api/users/login/", json=login_data)
        assert login_response.status_code == status.HTTP_200_OK
        
        # Now get profile using cookies (no Authorization header)
        response = client.get("/api/users/profile/")
        
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["email"] == "test@example.com"
