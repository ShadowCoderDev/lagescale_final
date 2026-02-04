"""Tests for product detail endpoints"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
from bson import ObjectId


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


class TestProductGet:
    """Tests for GET /api/products/{id}/"""
    
    @pytest.mark.asyncio
    async def test_get_product_success(self, client, mock_db):
        """Test getting product by ID"""
        mock_db.products.find_one = AsyncMock(return_value=MOCK_PRODUCT)
        
        response = await client.get("/api/products/507f1f77bcf86cd799439011/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Product"
        assert data["id"] == "507f1f77bcf86cd799439011"
    
    @pytest.mark.asyncio
    async def test_get_product_not_found(self, client, mock_db):
        """Test getting non-existent product"""
        mock_db.products.find_one = AsyncMock(return_value=None)
        
        response = await client.get("/api/products/507f1f77bcf86cd799439012/")
        
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_get_product_invalid_id(self, client, mock_db):
        """Test getting product with invalid ID - returns 404 for invalid IDs"""
        response = await client.get("/api/products/invalid-id/")
        
        # API returns 404 for all not found cases including invalid ID
        assert response.status_code == 404


class TestProductUpdate:
    """Tests for PUT /api/products/{id}/"""
    
    @pytest.mark.asyncio
    async def test_update_product_success(self, client, mock_db, admin_token):
        """Test updating product as admin"""
        mock_db.products.find_one = AsyncMock(return_value=MOCK_PRODUCT)
        mock_db.products.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
        
        updated_product = MOCK_PRODUCT.copy()
        updated_product["name"] = "Updated Product"
        mock_db.products.find_one = AsyncMock(
            side_effect=[MOCK_PRODUCT, MOCK_PRODUCT, updated_product]
        )
        
        update_data = {"name": "Updated Product"}
        
        response = await client.put(
            "/api/products/507f1f77bcf86cd799439011/",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_update_product_unauthorized(self, client, mock_db):
        """Test updating product without authentication"""
        update_data = {"name": "Updated Product"}
        
        response = await client.put(
            "/api/products/507f1f77bcf86cd799439011/",
            json=update_data
        )
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_update_product_not_admin(self, client, mock_db, user_token):
        """Test updating product as non-admin"""
        update_data = {"name": "Updated Product"}
        
        response = await client.put(
            "/api/products/507f1f77bcf86cd799439011/",
            json=update_data,
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_update_product_not_found(self, client, mock_db, admin_token):
        """Test updating non-existent product"""
        mock_db.products.find_one = AsyncMock(return_value=None)
        
        update_data = {"name": "Updated Product"}
        
        response = await client.put(
            "/api/products/507f1f77bcf86cd799439012/",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 404


class TestProductDelete:
    """Tests for DELETE /api/products/{id}/"""
    
    @pytest.mark.asyncio
    async def test_delete_product_success(self, client, mock_db, admin_token):
        """Test deleting product as admin (soft delete)"""
        mock_db.products.find_one = AsyncMock(return_value=MOCK_PRODUCT)
        mock_db.products.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
        
        response = await client.delete(
            "/api/products/507f1f77bcf86cd799439011/",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 204
    
    @pytest.mark.asyncio
    async def test_delete_product_unauthorized(self, client, mock_db):
        """Test deleting product without authentication"""
        response = await client.delete("/api/products/507f1f77bcf86cd799439011/")
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_delete_product_not_admin(self, client, mock_db, user_token):
        """Test deleting product as non-admin"""
        response = await client.delete(
            "/api/products/507f1f77bcf86cd799439011/",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_delete_product_not_found(self, client, mock_db, admin_token):
        """Test deleting non-existent product"""
        mock_db.products.find_one = AsyncMock(return_value=None)
        
        response = await client.delete(
            "/api/products/507f1f77bcf86cd799439012/",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 404
