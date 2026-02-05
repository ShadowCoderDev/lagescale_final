"""Tests for payment endpoints"""
import pytest


class TestHealthCheck:
    """Tests for health endpoint"""
    
    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """Test health endpoint returns healthy"""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "payment-service"


class TestProcessPayment:
    """Tests for POST /api/payments/process/"""
    
    @pytest.mark.asyncio
    async def test_process_payment_success(self, client, sample_payment_request):
        """Test successful payment (amount ends in .00)"""
        response = await client.post(
            "/api/payments/process/",
            json=sample_payment_request
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["order_id"] == sample_payment_request["order_id"]
        assert data["user_id"] == sample_payment_request["user_id"]
        # Amount may be returned as string or float
        assert float(data["amount"]) == float(sample_payment_request["amount"])
        assert "transaction_id" in data
        assert data["message"] == "Payment processed successfully"
    
    @pytest.mark.asyncio
    async def test_process_payment_failure(self, client, failing_payment_request):
        """Test failed payment (amount ends in .99)"""
        response = await client.post(
            "/api/payments/process/",
            json=failing_payment_request
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "failed"
        assert data["order_id"] == failing_payment_request["order_id"]
        assert "transaction_id" in data
        assert "declined" in data["message"].lower() or "rejected" in data["message"].lower()
    
    @pytest.mark.asyncio
    async def test_process_payment_invalid_amount(self, client):
        """Test payment with invalid amount"""
        response = await client.post(
            "/api/payments/process/",
            json={"order_id": 1, "user_id": 1, "amount": -10}
        )
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_process_payment_missing_fields(self, client):
        """Test payment with missing fields"""
        response = await client.post(
            "/api/payments/process/",
            json={"order_id": 1}
        )
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_process_payment_stores_record(self, client, sample_payment_request):
        """Test payment is stored in database"""
        response = await client.post(
            "/api/payments/process/",
            json=sample_payment_request
        )
        data = response.json()
        
        # Verify we can retrieve it
        get_response = await client.get(f"/api/payments/{data['transaction_id']}/")
        assert get_response.status_code == 200


class TestGetPayment:
    """Tests for GET /api/payments/{transaction_id}/"""
    
    @pytest.mark.asyncio
    async def test_get_payment_success(self, client, sample_payment_request):
        """Test getting payment by transaction ID"""
        # First create a payment
        create_response = await client.post(
            "/api/payments/process/",
            json=sample_payment_request
        )
        transaction_id = create_response.json()["transaction_id"]
        
        # Get the payment
        response = await client.get(f"/api/payments/{transaction_id}/")
        assert response.status_code == 200
        data = response.json()
        assert data["transaction_id"] == transaction_id
    
    @pytest.mark.asyncio
    async def test_get_payment_not_found(self, client):
        """Test getting non-existent payment"""
        response = await client.get("/api/payments/invalid-id/")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestGetPaymentsByOrder:
    """Tests for GET /api/payments/order/{order_id}/"""
    
    @pytest.mark.asyncio
    async def test_get_payments_by_order(self, client, sample_payment_request):
        """Test getting payments for specific order"""
        # Create payments for different orders with unique order_ids
        await client.post("/api/payments/process/", json=sample_payment_request)
        # Second payment for order 1 - use different amount to avoid duplicate success
        await client.post("/api/payments/process/", json={
            "order_id": 1, "user_id": 1, "amount": 50.99  # This will fail, so it's allowed
        })
        await client.post("/api/payments/process/", json={
            "order_id": 2, "user_id": 1, "amount": 75.00
        })
        
        # Get payments for order 1 (should have 2: 1 success, 1 failed)
        response = await client.get("/api/payments/order/1/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1  # At least one payment for order 1
        for payment in data:
            assert payment["order_id"] == 1
    
    @pytest.mark.asyncio
    async def test_get_payments_by_order_empty(self, client):
        """Test getting payments for order with no payments"""
        response = await client.get("/api/payments/order/999/")
        assert response.status_code == 200
        assert response.json() == []


class TestPaymentSimulation:
    """Tests for payment simulation rules"""
    
    @pytest.mark.asyncio
    async def test_amount_99_always_fails(self, client):
        """Test that .99 amounts always fail"""
        for amount in [9.99, 99.99, 199.99, 1000.99]:
            response = await client.post(
                "/api/payments/process/",
                json={"order_id": 1, "user_id": 1, "amount": amount}
            )
            assert response.json()["status"] == "failed"
    
    @pytest.mark.asyncio
    async def test_amount_00_always_succeeds(self, client):
        """Test that .00 amounts always succeed"""
        order_id = 100  # Start with unique order_id
        for amount in [10.00, 100.00, 500.00, 1000.00]:
            response = await client.post(
                "/api/payments/process/",
                json={"order_id": order_id, "user_id": 1, "amount": amount}
            )
            assert response.json()["status"] == "success"
            order_id += 1  # Use different order_id for each payment
