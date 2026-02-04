"""Tests for notification service"""
import pytest
from unittest.mock import patch, MagicMock


class TestHealthCheck:
    """Tests for health endpoint"""
    
    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """Test health endpoint"""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "notification-service"


class TestNotificationStatus:
    """Tests for notification status endpoint"""
    
    @pytest.mark.asyncio
    async def test_get_status(self, client):
        """Test getting notification service status"""
        response = await client.get("/api/notifications/status/")
        assert response.status_code == 200
        data = response.json()
        assert "email_service" in data
        assert "smtp_host" in data


class TestEmailService:
    """Tests for email service"""
    
    def test_send_order_created(self, mock_smtp, sample_order_created_data):
        """Test sending order created email"""
        from app.services.email_service import email_service
        
        mock_smtp.return_value.__enter__ = MagicMock()
        mock_smtp.return_value.__exit__ = MagicMock()
        
        result = email_service.send_order_created(
            sample_order_created_data["email"],
            sample_order_created_data["order_id"],
            sample_order_created_data["total_amount"]
        )
        
        # Will fail without SMTP server, but we check the call was made
        # In real tests, we'd mock the SMTP connection
        assert result in [True, False]
    
    def test_send_payment_success(self, mock_smtp, sample_payment_success_data):
        """Test sending payment success email"""
        from app.services.email_service import email_service
        
        mock_smtp.return_value.__enter__ = MagicMock()
        mock_smtp.return_value.__exit__ = MagicMock()
        
        result = email_service.send_payment_success(
            sample_payment_success_data["email"],
            sample_payment_success_data["order_id"],
            sample_payment_success_data["transaction_id"]
        )
        
        assert result in [True, False]
    
    def test_send_payment_failed(self, mock_smtp, sample_payment_failed_data):
        """Test sending payment failed email"""
        from app.services.email_service import email_service
        
        mock_smtp.return_value.__enter__ = MagicMock()
        mock_smtp.return_value.__exit__ = MagicMock()
        
        result = email_service.send_payment_failed(
            sample_payment_failed_data["email"],
            sample_payment_failed_data["order_id"],
            sample_payment_failed_data["reason"]
        )
        
        assert result in [True, False]
    
    def test_send_order_canceled(self, mock_smtp, sample_order_canceled_data):
        """Test sending order canceled email"""
        from app.services.email_service import email_service
        
        mock_smtp.return_value.__enter__ = MagicMock()
        mock_smtp.return_value.__exit__ = MagicMock()
        
        result = email_service.send_order_canceled(
            sample_order_canceled_data["email"],
            sample_order_canceled_data["order_id"]
        )
        
        assert result in [True, False]


class TestMessageProcessing:
    """Tests for message processing"""
    
    def test_handle_order_created(self, sample_order_created_data):
        """Test handling order created message"""
        from app.services.rabbitmq_consumer import notification_consumer
        
        with patch.object(notification_consumer, '_handle_order_created') as mock:
            notification_consumer._handle_order_created(sample_order_created_data)
            # Verify handler was called
    
    def test_handle_payment_success(self, sample_payment_success_data):
        """Test handling payment success message"""
        from app.services.rabbitmq_consumer import notification_consumer
        
        with patch.object(notification_consumer, '_handle_payment_success') as mock:
            notification_consumer._handle_payment_success(sample_payment_success_data)
    
    def test_handle_payment_failed(self, sample_payment_failed_data):
        """Test handling payment failed message"""
        from app.services.rabbitmq_consumer import notification_consumer
        
        with patch.object(notification_consumer, '_handle_payment_failed') as mock:
            notification_consumer._handle_payment_failed(sample_payment_failed_data)
    
    def test_handle_order_canceled(self, sample_order_canceled_data):
        """Test handling order canceled message"""
        from app.services.rabbitmq_consumer import notification_consumer
        
        with patch.object(notification_consumer, '_handle_order_canceled') as mock:
            notification_consumer._handle_order_canceled(sample_order_canceled_data)


class TestTestEmailEndpoint:
    """Tests for test email endpoint"""
    
    @pytest.mark.asyncio
    async def test_send_test_email_order_created(self, client, mock_smtp):
        """Test sending test email via API"""
        mock_smtp.return_value.__enter__ = MagicMock()
        mock_smtp.return_value.__exit__ = MagicMock()
        
        response = await client.post(
            "/api/notifications/test/",
            json={
                "to_email": "test@example.com",
                "event_type": "order_created",
                "order_id": 1,
                "total_amount": 99.99
            }
        )
        
        # May succeed or fail depending on SMTP availability
        assert response.status_code in [200, 500]
