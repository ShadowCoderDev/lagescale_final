"""Tests for search and stock endpoints"""
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


class TestProductSearch:
    """Tests for GET /api/products/search/"""
    
    @pytest.mark.asyncio
    async def test_search_products_success(self, client, mock_db):
        """Test searching products"""
        mock_db.products.count_documents = AsyncMock(return_value=1)
        mock_cursor = MagicMock()
        mock_cursor.sort = MagicMock(return_value=mock_cursor)
        mock_cursor.skip = MagicMock(return_value=mock_cursor)
        mock_cursor.limit = MagicMock(return_value=mock_cursor)
        mock_cursor.to_list = AsyncMock(return_value=[MOCK_PRODUCT])
        mock_db.products.find = MagicMock(return_value=mock_cursor)
        
        response = await client.get("/api/products/search/?q=Test")
        
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert len(data["results"]) == 1
    
    @pytest.mark.asyncio
    async def test_search_products_no_results(self, client, mock_db):
        """Test searching products with no results"""
        mock_db.products.count_documents = AsyncMock(return_value=0)
        mock_cursor = MagicMock()
        mock_cursor.sort = MagicMock(return_value=mock_cursor)
        mock_cursor.skip = MagicMock(return_value=mock_cursor)
        mock_cursor.limit = MagicMock(return_value=mock_cursor)
        mock_cursor.to_list = AsyncMock(return_value=[])
        mock_db.products.find = MagicMock(return_value=mock_cursor)
        
        response = await client.get("/api/products/search/?q=nonexistent")
        
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert data["results"] == []
    
    @pytest.mark.asyncio
    async def test_search_products_with_category(self, client, mock_db):
        """Test searching products with category filter"""
        mock_db.products.count_documents = AsyncMock(return_value=1)
        mock_cursor = MagicMock()
        mock_cursor.sort = MagicMock(return_value=mock_cursor)
        mock_cursor.skip = MagicMock(return_value=mock_cursor)
        mock_cursor.limit = MagicMock(return_value=mock_cursor)
        mock_cursor.to_list = AsyncMock(return_value=[MOCK_PRODUCT])
        mock_db.products.find = MagicMock(return_value=mock_cursor)
        
        response = await client.get("/api/products/search/?q=Test&category=Electronics")
        
        assert response.status_code == 200


class TestProductStock:
    """Tests for GET /api/products/{id}/stock/"""
    
    @pytest.mark.asyncio
    async def test_get_stock_success(self, client, mock_db):
        """Test getting product stock"""
        mock_db.products.find_one = AsyncMock(return_value=MOCK_PRODUCT)
        
        response = await client.get("/api/products/507f1f77bcf86cd799439011/stock/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["product_id"] == "507f1f77bcf86cd799439011"
        assert data["stock_quantity"] == 10
        assert data["in_stock"] == True
        assert data["available"] == True
    
    @pytest.mark.asyncio
    async def test_get_stock_out_of_stock(self, client, mock_db):
        """Test getting stock for out of stock product"""
        out_of_stock_product = MOCK_PRODUCT.copy()
        out_of_stock_product["stockQuantity"] = 0
        mock_db.products.find_one = AsyncMock(return_value=out_of_stock_product)
        
        response = await client.get("/api/products/507f1f77bcf86cd799439011/stock/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["stock_quantity"] == 0
        assert data["in_stock"] == False
    
    @pytest.mark.asyncio
    async def test_get_stock_not_found(self, client, mock_db):
        """Test getting stock for non-existent product"""
        mock_db.products.find_one = AsyncMock(return_value=None)
        
        response = await client.get("/api/products/507f1f77bcf86cd799439012/stock/")
        
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_get_stock_invalid_id(self, client, mock_db):
        """Test getting stock with invalid ID - returns 404 for invalid IDs"""
        response = await client.get("/api/products/invalid-id/stock/")
        
        # API returns 404 for all not found cases including invalid ID
        assert response.status_code == 404
