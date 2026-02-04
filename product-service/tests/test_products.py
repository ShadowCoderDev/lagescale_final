"""Tests for product list and create endpoints"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
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


class TestProductList:
    """Tests for GET /api/products/"""
    
    @pytest.mark.asyncio
    async def test_list_products_empty(self, client, mock_db):
        """Test listing products when empty"""
        mock_db.products.count_documents = AsyncMock(return_value=0)
        mock_cursor = MagicMock()
        mock_cursor.sort = MagicMock(return_value=mock_cursor)
        mock_cursor.skip = MagicMock(return_value=mock_cursor)
        mock_cursor.limit = MagicMock(return_value=mock_cursor)
        mock_cursor.to_list = AsyncMock(return_value=[])
        mock_db.products.find = MagicMock(return_value=mock_cursor)
        
        response = await client.get("/api/products/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert data["results"] == []
    
    @pytest.mark.asyncio
    async def test_list_products_with_data(self, client, mock_db):
        """Test listing products with data"""
        mock_db.products.count_documents = AsyncMock(return_value=1)
        mock_cursor = MagicMock()
        mock_cursor.sort = MagicMock(return_value=mock_cursor)
        mock_cursor.skip = MagicMock(return_value=mock_cursor)
        mock_cursor.limit = MagicMock(return_value=mock_cursor)
        mock_cursor.to_list = AsyncMock(return_value=[MOCK_PRODUCT])
        mock_db.products.find = MagicMock(return_value=mock_cursor)
        
        response = await client.get("/api/products/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert len(data["results"]) == 1
        assert data["results"][0]["name"] == "Test Product"
    
    @pytest.mark.asyncio
    async def test_list_products_with_category_filter(self, client, mock_db):
        """Test listing products with category filter"""
        mock_db.products.count_documents = AsyncMock(return_value=1)
        mock_cursor = MagicMock()
        mock_cursor.sort = MagicMock(return_value=mock_cursor)
        mock_cursor.skip = MagicMock(return_value=mock_cursor)
        mock_cursor.limit = MagicMock(return_value=mock_cursor)
        mock_cursor.to_list = AsyncMock(return_value=[MOCK_PRODUCT])
        mock_db.products.find = MagicMock(return_value=mock_cursor)
        
        response = await client.get("/api/products/?category=Electronics")
        
        assert response.status_code == 200
        mock_db.products.find.assert_called()


class TestProductCreate:
    """Tests for POST /api/products/"""
    
    @pytest.mark.asyncio
    async def test_create_product_success(self, client, mock_db, admin_token):
        """Test creating product as admin"""
        mock_db.products.find_one = AsyncMock(return_value=None)
        mock_db.products.insert_one = AsyncMock(
            return_value=MagicMock(inserted_id=ObjectId("507f1f77bcf86cd799439011"))
        )
        
        product_data = {
            "name": "New Product",
            "description": "New description",
            "price": 49.99,
            "stockQuantity": 5,
            "category": "Books",
            "sku": "NEW-001"
        }
        
        response = await client.post(
            "/api/products/",
            json=product_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Product"
        assert data["sku"] == "NEW-001"
    
    @pytest.mark.asyncio
    async def test_create_product_unauthorized(self, client, mock_db):
        """Test creating product without authentication"""
        product_data = {
            "name": "New Product",
            "price": 49.99,
            "stockQuantity": 5,
            "category": "Books",
            "sku": "NEW-001"
        }
        
        response = await client.post("/api/products/", json=product_data)
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_create_product_not_admin(self, client, mock_db, user_token):
        """Test creating product as non-admin"""
        product_data = {
            "name": "New Product",
            "price": 49.99,
            "stockQuantity": 5,
            "category": "Books",
            "sku": "NEW-001"
        }
        
        response = await client.post(
            "/api/products/",
            json=product_data,
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_create_product_duplicate_sku(self, client, mock_db, admin_token):
        """Test creating product with duplicate SKU"""
        mock_db.products.find_one = AsyncMock(return_value=MOCK_PRODUCT)
        
        product_data = {
            "name": "New Product",
            "price": 49.99,
            "stockQuantity": 5,
            "category": "Books",
            "sku": "TEST-001"
        }
        
        response = await client.post(
            "/api/products/",
            json=product_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 400
        assert "SKU" in response.json()["detail"]
