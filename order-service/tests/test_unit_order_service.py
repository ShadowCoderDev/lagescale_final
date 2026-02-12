"""Unit tests for OrderService business logic"""
import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import datetime

from app.services.order_service import OrderService, OrderServiceError, SagaState
from app.models.order import Order, OrderItem, OrderStatus


class TestSagaState:
    """Tests for SagaState dataclass"""

    def test_initial_state(self):
        saga = SagaState()
        assert saga.reservations == []
        assert saga.order_id is None
        assert saga.payment_transaction_id is None
        assert saga.stock_confirmed is False


class TestValidateProducts:
    """Unit tests for _validate_products"""

    @patch("app.services.order_service.product_client")
    def test_product_not_found(self, mock_product):
        mock_product.get_product.return_value = None

        service = OrderService(MagicMock())
        item = MagicMock()
        item.product_id = "nonexistent"
        item.quantity = 1

        with pytest.raises(OrderServiceError, match="یافت نشد"):
            service._validate_products([item])

    @patch("app.services.order_service.product_client")
    def test_inactive_product(self, mock_product):
        mock_product.get_product.return_value = {
            "id": "p1", "name": "Inactive Product",
            "price": 100, "isActive": False
        }

        service = OrderService(MagicMock())
        item = MagicMock()
        item.product_id = "p1"
        item.quantity = 1

        with pytest.raises(OrderServiceError, match="موجود نیست"):
            service._validate_products([item])

    @patch("app.services.order_service.product_client")
    def test_valid_products_calculate_total(self, mock_product):
        mock_product.get_product.side_effect = [
            {"id": "p1", "name": "Product A", "price": 50, "isActive": True},
            {"id": "p2", "name": "Product B", "price": 30, "isActive": True},
        ]

        service = OrderService(MagicMock())
        item1 = MagicMock()
        item1.product_id = "p1"
        item1.quantity = 2
        item2 = MagicMock()
        item2.product_id = "p2"
        item2.quantity = 3

        validated, total = service._validate_products([item1, item2])
        assert len(validated) == 2
        assert total == Decimal("190")  # 50*2 + 30*3
        assert validated[0]["product_name"] == "Product A"
        assert validated[1]["subtotal"] == Decimal("90")


class TestReserveStock:
    """Unit tests for _reserve_stock"""

    @patch("app.services.order_service.product_client")
    def test_reserve_success(self, mock_product):
        mock_product.reserve_stock.return_value = {
            "reservation_id": "res-1", "status": "reserved"
        }

        service = OrderService(MagicMock())
        saga = SagaState()
        items = [{"product_id": "p1", "product_name": "Test", "quantity": 2}]

        service._reserve_stock(items, saga)
        assert len(saga.reservations) == 1
        assert saga.reservations[0]["reservation_id"] == "res-1"
        assert items[0]["reservation_id"] == "res-1"

    @patch("app.services.order_service.product_client")
    def test_reserve_fails_insufficient_stock(self, mock_product):
        mock_product.reserve_stock.return_value = None

        service = OrderService(MagicMock())
        saga = SagaState()
        items = [{"product_id": "p1", "product_name": "Widget", "quantity": 100}]

        with pytest.raises(OrderServiceError, match="موجودی.*کافی نیست"):
            service._reserve_stock(items, saga)


class TestProcessPayment:
    """Unit tests for _process_payment"""

    @patch("app.services.order_service.payment_client")
    def test_payment_success(self, mock_payment):
        mock_payment.process_payment.return_value = {
            "status": "success", "transaction_id": "txn-123"
        }

        db = MagicMock()
        service = OrderService(db)
        saga = SagaState()
        order = MagicMock(spec=Order)
        order.id = 1

        service._process_payment(order, user_id=1, amount=Decimal("100"), saga=saga)
        assert saga.payment_transaction_id == "txn-123"

    @patch("app.services.order_service.payment_client")
    def test_payment_failure_sets_order_failed(self, mock_payment):
        mock_payment.process_payment.return_value = {
            "status": "failed", "message": "Declined"
        }

        db = MagicMock()
        service = OrderService(db)
        service.repository = MagicMock()
        saga = SagaState()
        order = MagicMock(spec=Order)
        order.id = 1

        with pytest.raises(OrderServiceError):
            service._process_payment(order, user_id=1, amount=Decimal("100"), saga=saga)

        service.repository.update_status.assert_called_once()


class TestConfirmStock:
    """Unit tests for _confirm_stock"""

    @patch("app.services.order_service.payment_client")
    @patch("app.services.order_service.product_client")
    def test_confirm_all_success(self, mock_product, mock_payment):
        mock_product.confirm_stock.return_value = True

        service = OrderService(MagicMock())
        saga = SagaState()
        saga.reservations = [
            {"product_id": "p1", "quantity": 1, "reservation_id": "r1"},
            {"product_id": "p2", "quantity": 2, "reservation_id": "r2"},
        ]
        saga.payment_transaction_id = "txn-1"

        service._confirm_stock(saga)
        assert saga.stock_confirmed is True

    @patch("app.services.order_service.payment_client")
    @patch("app.services.order_service.product_client")
    def test_confirm_failure_triggers_refund(self, mock_product, mock_payment):
        mock_product.confirm_stock.return_value = False
        mock_payment.refund.return_value = {"success": True}

        service = OrderService(MagicMock())
        saga = SagaState()
        saga.reservations = [
            {"product_id": "p1", "quantity": 1, "reservation_id": "r1"}
        ]
        saga.payment_transaction_id = "txn-1"

        with pytest.raises(OrderServiceError, match="خطا در تایید موجودی"):
            service._confirm_stock(saga)

        mock_payment.refund.assert_called_once()


class TestCompensation:
    """Unit tests for Saga compensation"""

    @patch("app.services.order_service.payment_client")
    @patch("app.services.order_service.product_client")
    def test_compensate_releases_stock(self, mock_product, mock_payment):
        db = MagicMock()
        service = OrderService(db)
        saga = SagaState()
        saga.reservations = [
            {"product_id": "p1", "reservation_id": "r1"},
            {"product_id": "p2", "reservation_id": "r2"},
        ]

        service._compensate(saga)
        assert mock_product.release_stock.call_count == 2

    @patch("app.services.order_service.payment_client")
    @patch("app.services.order_service.product_client")
    def test_compensate_refunds_payment(self, mock_product, mock_payment):
        db = MagicMock()
        service = OrderService(db)
        saga = SagaState()
        saga.payment_transaction_id = "txn-refund"
        saga.stock_confirmed = False

        service._compensate(saga)
        mock_payment.refund.assert_called_once_with("txn-refund", "Saga compensation")

    @patch("app.services.order_service.payment_client")
    @patch("app.services.order_service.product_client")
    def test_compensate_skips_refund_if_stock_confirmed(self, mock_product, mock_payment):
        db = MagicMock()
        service = OrderService(db)
        saga = SagaState()
        saga.payment_transaction_id = "txn-ok"
        saga.stock_confirmed = True

        service._compensate(saga)
        mock_payment.refund.assert_not_called()

    @patch("app.services.order_service.payment_client")
    @patch("app.services.order_service.product_client")
    def test_compensate_updates_order_to_failed(self, mock_product, mock_payment):
        order = MagicMock(spec=Order)
        order.status = OrderStatus.RESERVED

        db = MagicMock()
        service = OrderService(db)
        service.repository = MagicMock()
        service.repository.get_by_id.return_value = order

        saga = SagaState()
        saga.order_id = 1

        service._compensate(saga)
        service.repository.update_status.assert_called_once_with(order, OrderStatus.FAILED)


class TestCancelOrder:
    """Unit tests for cancel_order"""

    def _make_order(self, status, payment_id=None, items=None):
        order = MagicMock(spec=Order)
        order.id = 1
        order.user_id = 1
        order.status = status
        order.payment_id = payment_id
        order.items = items or []
        return order

    @patch("app.services.order_service.product_client")
    def test_cancel_not_found(self, mock_product):
        db = MagicMock()
        service = OrderService(db)
        service.repository = MagicMock()
        service.repository.get_by_id_and_user.return_value = None

        with pytest.raises(OrderServiceError) as exc_info:
            service.cancel_order(999, 1)
        assert exc_info.value.status_code == 404

    @patch("app.services.order_service.product_client")
    def test_cancel_already_canceled(self, mock_product):
        order = self._make_order(OrderStatus.CANCELED)
        db = MagicMock()
        service = OrderService(db)
        service.repository = MagicMock()
        service.repository.get_by_id_and_user.return_value = order

        with pytest.raises(OrderServiceError, match="قبلاً لغو شده"):
            service.cancel_order(1, 1)

    @patch("app.services.order_service.product_client")
    def test_cancel_shipped_rejected(self, mock_product):
        order = self._make_order(OrderStatus.SHIPPED)
        db = MagicMock()
        service = OrderService(db)
        service.repository = MagicMock()
        service.repository.get_by_id_and_user.return_value = order

        with pytest.raises(OrderServiceError, match="قابل لغو نیست"):
            service.cancel_order(1, 1)

    @patch("app.services.order_service.product_client")
    def test_cancel_failed_order_rejected(self, mock_product):
        order = self._make_order(OrderStatus.FAILED)
        db = MagicMock()
        service = OrderService(db)
        service.repository = MagicMock()
        service.repository.get_by_id_and_user.return_value = order

        with pytest.raises(OrderServiceError, match="ناموفق"):
            service.cancel_order(1, 1)

    @patch("app.services.order_service.product_client")
    def test_cancel_pending_releases_stock(self, mock_product):
        item = MagicMock()
        item.reservation_id = "res-1"
        order = self._make_order(OrderStatus.PENDING, items=[item])

        db = MagicMock()
        service = OrderService(db)
        service.repository = MagicMock()
        service.repository.get_by_id_and_user.return_value = order

        result = service.cancel_order(1, 1)
        mock_product.release_stock.assert_called_once()
        service.repository.update_status.assert_called_with(order, OrderStatus.CANCELED)

    @patch("app.services.order_service.payment_client")
    @patch("app.services.order_service.product_client")
    def test_cancel_paid_triggers_refund(self, mock_product, mock_payment):
        item = MagicMock()
        item.reservation_id = "res-1"
        order = self._make_order(OrderStatus.PAID, payment_id="txn-1", items=[item])

        mock_payment.refund.return_value = {"success": True}

        db = MagicMock()
        service = OrderService(db)
        service.repository = MagicMock()
        service.repository.get_by_id_and_user.return_value = order

        result = service.cancel_order(1, 1)
        mock_payment.refund.assert_called_once()
        service.repository.update_status.assert_called_with(order, OrderStatus.REFUNDED)


class TestGetOrder:
    """Unit tests for get_order"""

    def test_get_order_delegates_to_repository(self):
        db = MagicMock()
        service = OrderService(db)
        service.repository = MagicMock()
        expected = MagicMock(spec=Order)
        service.repository.get_by_id_and_user.return_value = expected

        result = service.get_order(1, 1)
        assert result == expected
        service.repository.get_by_id_and_user.assert_called_once_with(1, 1)


class TestListOrders:
    """Unit tests for list_orders"""

    def test_list_orders_with_filter(self):
        db = MagicMock()
        service = OrderService(db)
        service.repository = MagicMock()
        service.repository.list_by_user.return_value = ([], 0)

        orders, total = service.list_orders(1, status_filter=OrderStatus.PAID, page=2)
        service.repository.list_by_user.assert_called_once_with(1, OrderStatus.PAID, 2, 20)
        assert total == 0
