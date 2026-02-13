import logging
from decimal import Decimal
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.models.order import Order, OrderStatus
from app.repositories.order_repository import OrderRepository
from app.clients.product_client import product_client
from app.clients.payment_client import payment_client
from app.clients.notification_client import notification_publisher
from app.schemas.order import OrderCreate

logger = logging.getLogger(__name__)


@dataclass
class SagaState:
    reservations: List[Dict] = field(default_factory=list)
    order_id: Optional[int] = None
    payment_transaction_id: Optional[str] = None
    stock_confirmed: bool = False


class OrderServiceError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class OrderService:
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = OrderRepository(db)
    
    def checkout(self, order_data: OrderCreate, user_id: int, user_email: str = None) -> Order:
        saga = SagaState()
        
        try:
            if order_data.idempotency_key:
                existing = self.repository.get_by_idempotency_key(order_data.idempotency_key)
                if existing:
                    logger.info(f"Idempotency key found, returning order {existing.id}")
                    return existing
            
            validated_items, total_amount = self._validate_products(order_data.items)
            
            self._reserve_stock(validated_items, saga)
            
            order = self._create_order(
                user_id=user_id,
                total_amount=total_amount,
                items=validated_items,
                notes=order_data.notes,
                idempotency_key=order_data.idempotency_key
            )
            saga.order_id = order.id
            
            self._process_payment(order, user_id, total_amount, saga)
            
            self._confirm_stock(saga)
            
            self.repository.update_status(
                order, 
                OrderStatus.PAID, 
                payment_id=saga.payment_transaction_id
            )
            self.repository.commit()
            self.repository.refresh(order)
            
            logger.info(f"Saga: Order {order.id} completed successfully!")
            
            # Send notification (non-critical)
            self._send_success_notification(user_email, order)
            
            return order
            
        except OrderServiceError:
            self._compensate(saga)
            raise
        except Exception as e:
            logger.error(f"Saga: Unexpected error: {e}")
            self._compensate(saga)
            raise OrderServiceError(f"خطای غیرمنتظره: {str(e)}", 500)
    
    def get_order(self, order_id: int, user_id: int) -> Optional[Order]:
        return self.repository.get_by_id_and_user(order_id, user_id)
    
    def list_orders(
        self,
        user_id: int,
        status_filter: Optional[OrderStatus] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[Order], int]:
        return self.repository.list_by_user(user_id, status_filter, page, page_size)
    
    def cancel_order(self, order_id: int, user_id: int) -> Order:
        """
        PENDING/RESERVED: cancel and release stock.
        PAID: refund payment, release stock, mark REFUNDED.
        SHIPPED/DELIVERED: cannot cancel.
        """
        order = self.repository.get_by_id_and_user(order_id, user_id)
        
        if not order:
            raise OrderServiceError("سفارش یافت نشد", 404)
        
        # Already cancelled/refunded
        if order.status in [OrderStatus.CANCELED, OrderStatus.REFUNDED]:
            raise OrderServiceError("این سفارش قبلاً لغو شده است", 400)
        
        # Shipped/Delivered cannot be cancelled
        if order.status in [OrderStatus.SHIPPED, OrderStatus.DELIVERED]:
            raise OrderServiceError(
                "سفارش ارسال شده قابل لغو نیست. لطفاً درخواست مرجوعی ثبت کنید",
                400
            )
        
        # Failed orders don't need cancellation
        if order.status == OrderStatus.FAILED:
            raise OrderServiceError("این سفارش قبلاً ناموفق بوده است", 400)
        
        # Handle PAID orders - need refund
        if order.status == OrderStatus.PAID:
            if order.payment_id:
                refund_result = payment_client.refund(
                    transaction_id=order.payment_id,
                    reason="لغو سفارش توسط کاربر"
                )
                if not refund_result.get("success"):
                    raise OrderServiceError(
                        f"خطا در بازپرداخت: {refund_result.get('message', 'Unknown error')}",
                        500
                    )
                logger.info(f"Order {order_id} refunded: {refund_result.get('refund_id')}")
            
            # Release stock (if somehow still reserved)
            for item in order.items:
                if item.reservation_id:
                    product_client.release_stock(item.reservation_id, "Order refunded")
            
            self.repository.update_status(order, OrderStatus.REFUNDED)
            self.repository.commit()
            return order
        
        # Handle PENDING/RESERVED/PROCESSING - just cancel
        for item in order.items:
            if item.reservation_id:
                product_client.release_stock(item.reservation_id, "Order cancelled by user")
        
        self.repository.update_status(order, OrderStatus.CANCELED)
        self.repository.commit()
        
        return order
    
    def _validate_products(self, items) -> tuple[List[Dict], Decimal]:
        validated = []
        total = Decimal("0")
        
        for item in items:
            product = product_client.get_product(item.product_id)
            
            if not product:
                raise OrderServiceError(f"محصول یافت نشد: {item.product_id}")
            
            if not product.get("isActive", False):
                raise OrderServiceError(f"محصول {product.get('name')} موجود نیست")
            
            unit_price = Decimal(str(product.get("price", 0)))
            subtotal = unit_price * item.quantity
            total += subtotal
            
            validated.append({
                "product_id": item.product_id,
                "product_name": product.get("name"),
                "quantity": item.quantity,
                "unit_price": unit_price,
                "subtotal": subtotal
            })
        
        return validated, total
    
    def _reserve_stock(self, items: List[Dict], saga: SagaState):
        logger.info(f"Saga: Reserving stock for {len(items)} items")
        
        for item in items:
            reservation = product_client.reserve_stock(
                product_id=item["product_id"],
                quantity=item["quantity"],
                order_id=0  # Will update after order created
            )
            
            if not reservation:
                raise OrderServiceError(f"موجودی {item['product_name']} کافی نیست")
            
            saga.reservations.append({
                "product_id": item["product_id"],
                "quantity": item["quantity"],
                "reservation_id": reservation["reservation_id"]
            })
            item["reservation_id"] = reservation["reservation_id"]
        
        logger.info("Saga: All stock reserved")
    
    def _create_order(
        self,
        user_id: int,
        total_amount: Decimal,
        items: List[Dict],
        notes: str = None,
        idempotency_key: str = None
    ) -> Order:
        order = self.repository.create_order(
            user_id=user_id,
            total_amount=total_amount,
            status=OrderStatus.RESERVED,
            notes=notes,
            idempotency_key=idempotency_key
        )
        
        for item in items:
            self.repository.create_order_item(
                order_id=order.id,
                product_id=item["product_id"],
                product_name=item["product_name"],
                quantity=item["quantity"],
                unit_price=item["unit_price"],
                subtotal=item["subtotal"],
                reservation_id=item.get("reservation_id")
            )
        
        self.repository.commit()
        self.repository.refresh(order)
        
        logger.info(f"Saga: Order {order.id} created with RESERVED status")
        return order
    
    def _process_payment(
        self,
        order: Order,
        user_id: int,
        amount: Decimal,
        saga: SagaState
    ):
        logger.info(f"Saga: Processing payment for order {order.id}")
        
        result = payment_client.process_payment(
            order_id=order.id,
            user_id=user_id,
            amount=amount
        )
        
        if result.get("status") != "success":
            self.repository.update_status(
                order,
                OrderStatus.FAILED,
                failure_reason=result.get("message", "Payment failed")
            )
            self.repository.commit()
            raise OrderServiceError(result.get("message", "پرداخت ناموفق بود"))
        
        saga.payment_transaction_id = result.get("transaction_id")
        logger.info(f"Saga: Payment successful, transaction={saga.payment_transaction_id}")
    
    def _confirm_stock(self, saga: SagaState):
        logger.info("Saga: Confirming stock deduction")
        
        failures = []
        for res in saga.reservations:
            if not product_client.confirm_stock(res["reservation_id"]):
                failures.append(res["product_id"])
        
        if failures:
            # Refund payment
            logger.error(f"Saga: Stock confirmation failed for: {failures}")
            refund = payment_client.refund(
                saga.payment_transaction_id,
                reason=f"Stock confirmation failed"
            )
            
            if not refund.get("success"):
                logger.critical(f"CRITICAL: Refund failed for transaction {saga.payment_transaction_id}")
            
            raise OrderServiceError("خطا در تایید موجودی. پرداخت برگشت داده شد.", 500)
        
        saga.stock_confirmed = True
        logger.info("Saga: Stock confirmed")
    
    def _compensate(self, saga: SagaState):
        logger.warning("Saga Compensation triggered")
        
        # Refund if paid but not confirmed
        if saga.payment_transaction_id and not saga.stock_confirmed:
            try:
                payment_client.refund(saga.payment_transaction_id, "Saga compensation")
                logger.info("Compensation: Payment refunded")
            except Exception as e:
                logger.error(f"Compensation: Refund failed: {e}")
        
        # Release all reservations
        for res in saga.reservations:
            try:
                product_client.release_stock(res["reservation_id"], "Saga compensation")
                logger.info(f"Compensation: Stock released for {res['product_id']}")
            except Exception as e:
                logger.error(f"Compensation: Release failed: {e}")
        
        # Update order status
        if saga.order_id:
            try:
                order = self.repository.get_by_id(saga.order_id)
                if order and order.status not in [OrderStatus.PAID, OrderStatus.FAILED]:
                    self.repository.update_status(order, OrderStatus.FAILED)
                    self.repository.commit()
            except Exception as e:
                logger.error(f"Compensation: Order update failed: {e}")
    
    def _send_success_notification(self, email: str, order: Order):
        if not email:
            return
        try:
            notification_publisher.send_payment_success(
                email=email,
                order_id=order.id,
                transaction_id=order.payment_id or "N/A"
            )
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
    
    def _send_failure_notification(self, email: str, order_id: int, reason: str):
        if not email:
            return
        try:
            notification_publisher.send_payment_failed(
                email=email,
                order_id=order_id,
                reason=reason
            )
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
