"""Tests for order endpoints"""
import pytest
from unittest.mock import patch, MagicMock
from app.models.order import OrderStatus


class TestCreateOrder:
    """Tests for POST /api/orders/"""
    
    @pytest.mark.asyncio
    async def test_create_order_unauthorized(self, client):
        """Test creating order without auth"""
        response = await client.post("/api/orders/", json={
            "items": [{"product_id": "123", "quantity": 1}]
        })
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    @patch("app.api.orders.product_client")
    async def test_create_order_success(self, mock_product, client, user_token, db):
        """Test creating order successfully"""
        mock_product.get_product.return_value = {
            "id": "507f1f77bcf86cd799439011",
            "name": "Test Product",
            "price": 99.99,
            "stockQuantity": 10,
            "isActive": True
        }
        
        response = await client.post(
            "/api/orders/",
            json={
                "items": [{"product_id": "507f1f77bcf86cd799439011", "quantity": 2}],
                "notes": "Test order"
            },
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "PENDING"
        assert len(data["items"]) == 1
    
    @pytest.mark.asyncio
    @patch("app.api.orders.product_client")
    async def test_create_order_product_not_found(self, mock_product, client, user_token):
        """Test creating order with non-existent product"""
        mock_product.get_product.return_value = None
        
        response = await client.post(
            "/api/orders/",
            json={"items": [{"product_id": "invalid", "quantity": 1}]},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 400
        assert "not found" in response.json()["detail"]
    
    @pytest.mark.asyncio
    @patch("app.api.orders.product_client")
    async def test_create_order_insufficient_stock(self, mock_product, client, user_token):
        """Test creating order with insufficient stock"""
        mock_product.get_product.return_value = {
            "id": "123",
            "name": "Test",
            "price": 10,
            "stockQuantity": 1,
            "isActive": True
        }
        
        response = await client.post(
            "/api/orders/",
            json={"items": [{"product_id": "123", "quantity": 10}]},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 400
        assert "stock" in response.json()["detail"].lower()


class TestListOrders:
    """Tests for GET /api/orders/"""
    
    @pytest.mark.asyncio
    async def test_list_orders_unauthorized(self, client):
        """Test listing orders without auth"""
        response = await client.get("/api/orders/")
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_list_orders_empty(self, client, user_token, db):
        """Test listing orders when empty"""
        response = await client.get(
            "/api/orders/",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["orders"] == []
    
    @pytest.mark.asyncio
    async def test_list_orders_with_data(self, client, user_token, sample_order):
        """Test listing orders with data"""
        response = await client.get(
            "/api/orders/",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["orders"]) == 1


class TestGetOrder:
    """Tests for GET /api/orders/{id}"""
    
    @pytest.mark.asyncio
    async def test_get_order_unauthorized(self, client, sample_order):
        """Test getting order without auth"""
        response = await client.get(f"/api/orders/{sample_order.id}")
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_order_success(self, client, user_token, sample_order):
        """Test getting order successfully"""
        response = await client.get(
            f"/api/orders/{sample_order.id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_order.id
    
    @pytest.mark.asyncio
    async def test_get_order_not_found(self, client, user_token, db):
        """Test getting non-existent order"""
        response = await client.get(
            "/api/orders/999",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 404


class TestPayOrder:
    """Tests for POST /api/orders/{id}/pay"""
    
    @pytest.mark.asyncio
    async def test_pay_order_unauthorized(self, client, sample_order):
        """Test paying order without auth"""
        response = await client.post(f"/api/orders/{sample_order.id}/pay")
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    @patch("app.api.orders.payment_client")
    async def test_pay_order_success(self, mock_payment, client, user_token, sample_order):
        """Test paying order successfully"""
        mock_payment.process_payment.return_value = {
            "transaction_id": "txn_123",
            "status": "success",
            "message": "Payment successful"
        }
        
        response = await client.post(
            f"/api/orders/{sample_order.id}/pay",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "PAID"
        assert data["payment_id"] == "txn_123"
    
    @pytest.mark.asyncio
    @patch("app.api.orders.payment_client")
    async def test_pay_order_failed(self, mock_payment, client, user_token, sample_order):
        """Test payment failure"""
        mock_payment.process_payment.return_value = {
            "transaction_id": None,
            "status": "failed",
            "message": "Insufficient funds"
        }
        
        response = await client.post(
            f"/api/orders/{sample_order.id}/pay",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 400


class TestCancelOrder:
    """Tests for POST /api/orders/{id}/cancel"""
    
    @pytest.mark.asyncio
    async def test_cancel_order_unauthorized(self, client, sample_order):
        """Test cancelling order without auth"""
        response = await client.post(f"/api/orders/{sample_order.id}/cancel")
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_cancel_order_success(self, client, user_token, sample_order):
        """Test cancelling order successfully"""
        response = await client.post(
            f"/api/orders/{sample_order.id}/cancel",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 200
        assert "cancelled" in response.json()["message"].lower()
    
    @pytest.mark.asyncio
    async def test_cancel_order_not_found(self, client, user_token, db):
        """Test cancelling non-existent order"""
        response = await client.post(
            "/api/orders/999/cancel",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 404
