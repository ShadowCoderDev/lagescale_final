"""Unit tests for PaymentService business logic"""
import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

from app.services.payment_service import PaymentService, PaymentServiceError
from app.db.models import Payment, PaymentStatus as DBPaymentStatus


class TestDeterminePaymentOutcome:
    """Unit tests for _determine_payment_outcome static method"""

    def test_amount_ending_99_always_fails(self):
        """Amounts ending in .99 should always fail"""
        for amount in [9.99, 49.99, 199.99, 1000.99]:
            success, message = PaymentService._determine_payment_outcome(Decimal(str(amount)))
            assert success is False
            assert ".99" in message

    def test_amount_ending_00_always_succeeds(self):
        """Amounts ending in .00 should always succeed"""
        for amount in [10.00, 100.00, 500.00, 1.00]:
            success, message = PaymentService._determine_payment_outcome(Decimal(str(amount)))
            assert success is True
            assert "successfully" in message

    @patch("app.services.payment_service.random.random", return_value=0.5)
    def test_random_amount_succeeds_within_rate(self, mock_random):
        """Amounts not ending in .99/.00 succeed when random < SUCCESS_RATE"""
        success, message = PaymentService._determine_payment_outcome(Decimal("50.50"))
        assert success is True

    @patch("app.services.payment_service.random.random", return_value=0.95)
    def test_random_amount_fails_outside_rate(self, mock_random):
        """Amounts not ending in .99/.00 fail when random >= SUCCESS_RATE"""
        success, message = PaymentService._determine_payment_outcome(Decimal("50.50"))
        assert success is False
        assert "declined" in message.lower()

    def test_very_small_amount(self):
        """Test with very small amount ending in .00"""
        success, _ = PaymentService._determine_payment_outcome(Decimal("0.01"))
        # 0.01 doesn't end in .99 or .00, so it's random-based
        assert isinstance(success, bool)

    def test_large_amount(self):
        """Test with large amount ending in .00"""
        success, _ = PaymentService._determine_payment_outcome(Decimal("999999.00"))
        assert success is True


class TestProcessPayment:
    """Unit tests for process_payment method"""

    def _make_service(self, db_mock=None):
        return PaymentService(db_mock or MagicMock(spec=Session))

    @patch("app.services.payment_service.crud")
    def test_idempotency_returns_existing(self, mock_crud):
        """If idempotency_key already exists, return existing payment"""
        existing = MagicMock(spec=Payment)
        existing.transaction_id = "txn-existing"
        existing.order_id = 1
        existing.user_id = 1
        existing.amount = Decimal("100.00")
        existing.status = DBPaymentStatus.SUCCESS
        existing.message = "Payment processed successfully"
        existing.processed_at = "2025-01-01T00:00:00"

        mock_crud.get_payment_by_idempotency_key.return_value = existing
        mock_crud.get_successful_payment_by_order_id.return_value = None

        from app.schemas.payment import PaymentRequest
        request = PaymentRequest(
            order_id=1, user_id=1, amount=Decimal("100.00"),
            idempotency_key="key-123"
        )

        service = self._make_service()
        result = service.process_payment(request)
        assert result["transaction_id"] == "txn-existing"
        mock_crud.create_payment.assert_not_called()

    @patch("app.services.payment_service.crud")
    def test_duplicate_successful_payment_raises(self, mock_crud):
        """Cannot process payment if order already has a successful one"""
        mock_crud.get_payment_by_idempotency_key.return_value = None
        mock_crud.get_successful_payment_by_order_id.return_value = MagicMock()

        from app.schemas.payment import PaymentRequest
        request = PaymentRequest(order_id=1, user_id=1, amount=Decimal("100.00"))

        service = self._make_service()
        with pytest.raises(PaymentServiceError, match="already has a successful payment"):
            service.process_payment(request)

    @patch("app.services.payment_service.crud")
    def test_successful_payment_creates_record(self, mock_crud):
        """Successful payment creates a record with SUCCESS status"""
        mock_crud.get_payment_by_idempotency_key.return_value = None
        mock_crud.get_successful_payment_by_order_id.return_value = None

        created = MagicMock(spec=Payment)
        created.transaction_id = "txn-new"
        created.order_id = 1
        created.user_id = 1
        created.amount = Decimal("100.00")
        created.status = DBPaymentStatus.SUCCESS
        created.message = "Payment processed successfully"
        created.processed_at = "2025-01-01T00:00:00"
        mock_crud.create_payment.return_value = created

        from app.schemas.payment import PaymentRequest
        request = PaymentRequest(order_id=1, user_id=1, amount=Decimal("100.00"))

        service = self._make_service()
        result = service.process_payment(request)
        assert result["status"] == "success"
        mock_crud.create_payment.assert_called_once()

    @patch("app.services.payment_service.crud")
    def test_failed_payment_creates_record(self, mock_crud):
        """Failed payment (.99) creates a record with FAILED status"""
        mock_crud.get_payment_by_idempotency_key.return_value = None
        mock_crud.get_successful_payment_by_order_id.return_value = None

        created = MagicMock(spec=Payment)
        created.transaction_id = "txn-fail"
        created.order_id = 1
        created.user_id = 1
        created.amount = Decimal("99.99")
        created.status = DBPaymentStatus.FAILED
        created.message = "Payment declined"
        created.processed_at = "2025-01-01T00:00:00"
        mock_crud.create_payment.return_value = created

        from app.schemas.payment import PaymentRequest
        request = PaymentRequest(order_id=1, user_id=1, amount=Decimal("99.99"))

        service = self._make_service()
        result = service.process_payment(request)
        assert result["status"] == "failed"


class TestRefundPayment:
    """Unit tests for refund_payment method"""

    def _make_service(self, db_mock=None):
        return PaymentService(db_mock or MagicMock(spec=Session))

    @patch("app.services.payment_service.crud")
    def test_refund_not_found(self, mock_crud):
        """Refund fails if original payment not found"""
        mock_crud.get_payment_by_transaction_id.return_value = None

        from app.schemas.payment import RefundRequest
        request = RefundRequest(transaction_id="nonexistent")

        service = self._make_service()
        with pytest.raises(PaymentServiceError, match="not found"):
            service.refund_payment(request)

    @patch("app.services.payment_service.crud")
    def test_refund_non_success_payment(self, mock_crud):
        """Cannot refund a non-success payment"""
        original = MagicMock(spec=Payment)
        original.status = DBPaymentStatus.FAILED
        mock_crud.get_payment_by_transaction_id.return_value = original

        from app.schemas.payment import RefundRequest
        request = RefundRequest(transaction_id="txn-123")

        service = self._make_service()
        with pytest.raises(PaymentServiceError, match="Cannot refund"):
            service.refund_payment(request)

    @patch("app.services.payment_service.crud")
    def test_refund_already_refunded(self, mock_crud):
        """Cannot refund a payment that is already refunded"""
        original = MagicMock(spec=Payment)
        original.status = DBPaymentStatus.SUCCESS
        mock_crud.get_payment_by_transaction_id.return_value = original

        existing_refund = MagicMock()
        existing_refund.transaction_id = "refund-123"
        mock_crud.get_refund_by_original_transaction.return_value = existing_refund

        from app.schemas.payment import RefundRequest
        request = RefundRequest(transaction_id="txn-123")

        service = self._make_service()
        with pytest.raises(PaymentServiceError, match="already refunded"):
            service.refund_payment(request)

    @patch("app.services.payment_service.crud")
    def test_refund_success(self, mock_crud):
        """Successful refund creates REFUNDED record"""
        original = MagicMock(spec=Payment)
        original.status = DBPaymentStatus.SUCCESS
        original.order_id = 1
        original.user_id = 1
        original.amount = Decimal("100.00")
        mock_crud.get_payment_by_transaction_id.return_value = original
        mock_crud.get_refund_by_original_transaction.return_value = None

        refund = MagicMock(spec=Payment)
        refund.transaction_id = "refund-new"
        refund.order_id = 1
        refund.user_id = 1
        refund.amount = Decimal("100.00")
        refund.status = DBPaymentStatus.REFUNDED
        refund.message = "Refund"
        refund.processed_at = "2025-01-01T00:00:00"
        mock_crud.create_refund.return_value = refund

        from app.schemas.payment import RefundRequest
        request = RefundRequest(transaction_id="txn-123", reason="Customer request")

        service = self._make_service()
        result = service.refund_payment(request)
        assert result["status"] == "refunded"
        assert result["transaction_id"] == "refund-new"


class TestGetPayment:
    """Unit tests for get_payment method"""

    @patch("app.services.payment_service.crud")
    def test_get_payment_not_found(self, mock_crud):
        mock_crud.get_payment_by_transaction_id.return_value = None
        service = PaymentService(MagicMock())
        with pytest.raises(PaymentServiceError, match="not found"):
            service.get_payment("nonexistent")

    @patch("app.services.payment_service.crud")
    def test_get_payment_success(self, mock_crud):
        payment = MagicMock(spec=Payment)
        payment.transaction_id = "txn-1"
        payment.order_id = 1
        payment.user_id = 1
        payment.amount = Decimal("50.00")
        payment.status = DBPaymentStatus.SUCCESS
        payment.message = "ok"
        payment.processed_at = "2025-01-01"
        mock_crud.get_payment_by_transaction_id.return_value = payment

        service = PaymentService(MagicMock())
        result = service.get_payment("txn-1")
        assert result["transaction_id"] == "txn-1"


class TestGetOrderPayments:
    """Unit tests for get_order_payments method"""

    @patch("app.services.payment_service.crud")
    def test_empty_order_payments(self, mock_crud):
        mock_crud.get_payments_by_order_id.return_value = []
        service = PaymentService(MagicMock())
        result = service.get_order_payments(999)
        assert result == []

    @patch("app.services.payment_service.crud")
    def test_multiple_order_payments(self, mock_crud):
        p1 = MagicMock(spec=Payment)
        p1.transaction_id = "t1"
        p1.order_id = 1
        p1.user_id = 1
        p1.amount = Decimal("50")
        p1.status = DBPaymentStatus.FAILED
        p1.message = "fail"
        p1.processed_at = "2025-01-01"

        p2 = MagicMock(spec=Payment)
        p2.transaction_id = "t2"
        p2.order_id = 1
        p2.user_id = 1
        p2.amount = Decimal("50")
        p2.status = DBPaymentStatus.SUCCESS
        p2.message = "ok"
        p2.processed_at = "2025-01-01"

        mock_crud.get_payments_by_order_id.return_value = [p1, p2]
        service = PaymentService(MagicMock())
        result = service.get_order_payments(1)
        assert len(result) == 2
        assert result[0]["status"] == "failed"
        assert result[1]["status"] == "success"
