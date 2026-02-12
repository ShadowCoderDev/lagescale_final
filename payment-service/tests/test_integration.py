"""Integration tests for Payment Service - full API flow via test client"""
import pytest


class TestPaymentFullFlow:
    """End-to-end integration tests for the payment lifecycle"""

    @pytest.mark.asyncio
    async def test_full_payment_lifecycle(self, client):
        """Test: process payment -> retrieve -> refund -> verify refund"""
        # Step 1: Process a successful payment
        pay_resp = await client.post("/api/payments/process/", json={
            "order_id": 50, "user_id": 1, "amount": 250.00
        })
        assert pay_resp.status_code == 200
        pay_data = pay_resp.json()
        assert pay_data["status"] == "success"
        txn_id = pay_data["transaction_id"]

        # Step 2: Retrieve the payment
        get_resp = await client.get(f"/api/payments/{txn_id}/")
        assert get_resp.status_code == 200
        assert get_resp.json()["transaction_id"] == txn_id
        assert get_resp.json()["status"] == "success"

        # Step 3: Refund the payment
        refund_resp = await client.post("/api/payments/refund/", json={
            "transaction_id": txn_id,
            "reason": "Customer changed mind"
        })
        assert refund_resp.status_code == 200
        refund_data = refund_resp.json()
        assert refund_data["status"] == "refunded"
        assert refund_data["order_id"] == 50
        assert float(refund_data["amount"]) == 250.00

        # Step 4: Verify both payments appear in order history
        order_resp = await client.get("/api/payments/order/50/")
        assert order_resp.status_code == 200
        payments = order_resp.json()
        assert len(payments) == 2
        statuses = {p["status"] for p in payments}
        assert statuses == {"success", "refunded"}

    @pytest.mark.asyncio
    async def test_double_refund_rejected(self, client):
        """Test that refunding the same payment twice is rejected"""
        # Create payment
        resp = await client.post("/api/payments/process/", json={
            "order_id": 60, "user_id": 1, "amount": 100.00
        })
        txn_id = resp.json()["transaction_id"]

        # First refund - should succeed
        refund1 = await client.post("/api/payments/refund/", json={
            "transaction_id": txn_id
        })
        assert refund1.status_code == 200

        # Second refund - should fail
        refund2 = await client.post("/api/payments/refund/", json={
            "transaction_id": txn_id
        })
        assert refund2.status_code == 400
        assert "already refunded" in refund2.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_refund_failed_payment_rejected(self, client):
        """Cannot refund a failed payment"""
        # Create a failed payment (.99 always fails)
        resp = await client.post("/api/payments/process/", json={
            "order_id": 70, "user_id": 1, "amount": 99.99
        })
        assert resp.json()["status"] == "failed"
        txn_id = resp.json()["transaction_id"]

        # Try to refund - should fail
        refund = await client.post("/api/payments/refund/", json={
            "transaction_id": txn_id
        })
        assert refund.status_code == 400
        assert "cannot refund" in refund.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_idempotency_full_flow(self, client):
        """Test idempotency key prevents duplicate payment creation"""
        payload = {
            "order_id": 80, "user_id": 1, "amount": 200.00,
            "idempotency_key": "idem-key-001"
        }

        # First request
        resp1 = await client.post("/api/payments/process/", json=payload)
        assert resp1.status_code == 200
        txn1 = resp1.json()["transaction_id"]

        # Second request with same key - should return same transaction
        resp2 = await client.post("/api/payments/process/", json=payload)
        assert resp2.status_code == 200
        txn2 = resp2.json()["transaction_id"]

        assert txn1 == txn2

        # Order should still have just 1 payment
        order_resp = await client.get("/api/payments/order/80/")
        assert len(order_resp.json()) == 1

    @pytest.mark.asyncio
    async def test_duplicate_success_payment_rejected(self, client):
        """Cannot process a second successful payment for the same order"""
        # First payment - success
        resp1 = await client.post("/api/payments/process/", json={
            "order_id": 90, "user_id": 1, "amount": 100.00
        })
        assert resp1.json()["status"] == "success"

        # Second payment for same order - should fail
        resp2 = await client.post("/api/payments/process/", json={
            "order_id": 90, "user_id": 1, "amount": 200.00
        })
        assert resp2.status_code == 400
        assert "already has a successful payment" in resp2.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_failed_then_success_same_order(self, client):
        """Can retry payment after a failed attempt"""
        # First - fails (.99)
        resp1 = await client.post("/api/payments/process/", json={
            "order_id": 100, "user_id": 1, "amount": 49.99
        })
        assert resp1.json()["status"] == "failed"

        # Second - succeeds (.00)
        resp2 = await client.post("/api/payments/process/", json={
            "order_id": 100, "user_id": 1, "amount": 50.00
        })
        assert resp2.json()["status"] == "success"

        # Should have 2 payments
        order_resp = await client.get("/api/payments/order/100/")
        assert len(order_resp.json()) == 2

    @pytest.mark.asyncio
    async def test_refund_nonexistent_payment(self, client):
        """Cannot refund a non-existent transaction"""
        refund = await client.post("/api/payments/refund/", json={
            "transaction_id": "does-not-exist"
        })
        assert refund.status_code == 404
        assert "not found" in refund.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_concurrent_order_payments(self, client):
        """Multiple orders can have successful payments independently"""
        results = []
        for order_id in range(200, 205):
            resp = await client.post("/api/payments/process/", json={
                "order_id": order_id, "user_id": 1, "amount": 100.00
            })
            assert resp.status_code == 200
            results.append(resp.json())

        # All should succeed
        assert all(r["status"] == "success" for r in results)
        # All should have unique transaction IDs
        txn_ids = [r["transaction_id"] for r in results]
        assert len(set(txn_ids)) == 5
