"""
Order Repository - Data Access Layer
Handles all database operations for orders
"""
import logging
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.order import Order, OrderItem, OrderStatus

logger = logging.getLogger(__name__)


class OrderRepository:
    """Repository for Order database operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ═══════════════════════════════════════════════════════════════
    # CREATE
    # ═══════════════════════════════════════════════════════════════
    
    def create_order(
        self,
        user_id: int,
        total_amount,
        status: OrderStatus = OrderStatus.PENDING,
        notes: str = None,
        idempotency_key: str = None
    ) -> Order:
        """Create a new order"""
        order = Order(
            user_id=user_id,
            total_amount=total_amount,
            status=status,
            notes=notes,
            idempotency_key=idempotency_key
        )
        self.db.add(order)
        self.db.flush()  # Get order.id without committing
        return order
    
    def create_order_item(
        self,
        order_id: int,
        product_id: str,
        product_name: str,
        quantity: int,
        unit_price,
        subtotal,
        reservation_id: str = None
    ) -> OrderItem:
        """Create an order item"""
        item = OrderItem(
            order_id=order_id,
            product_id=product_id,
            product_name=product_name,
            quantity=quantity,
            unit_price=unit_price,
            subtotal=subtotal,
            reservation_id=reservation_id
        )
        self.db.add(item)
        return item
    
    # ═══════════════════════════════════════════════════════════════
    # READ
    # ═══════════════════════════════════════════════════════════════
    
    def get_by_id(self, order_id: int) -> Optional[Order]:
        """Get order by ID"""
        return self.db.query(Order).filter(Order.id == order_id).first()
    
    def get_by_id_and_user(self, order_id: int, user_id: int) -> Optional[Order]:
        """Get order by ID for a specific user"""
        return self.db.query(Order).filter(
            Order.id == order_id,
            Order.user_id == user_id
        ).first()
    
    def get_by_idempotency_key(self, key: str) -> Optional[Order]:
        """Get order by idempotency key"""
        return self.db.query(Order).filter(
            Order.idempotency_key == key
        ).first()
    
    def list_by_user(
        self,
        user_id: int,
        status_filter: Optional[OrderStatus] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[Order], int]:
        """
        List orders for a user with pagination
        Returns (orders, total_count)
        """
        query = self.db.query(Order).filter(Order.user_id == user_id)
        
        if status_filter:
            query = query.filter(Order.status == status_filter)
        
        total = query.count()
        
        orders = query.order_by(desc(Order.created_at)) \
            .offset((page - 1) * page_size) \
            .limit(page_size) \
            .all()
        
        return orders, total
    
    # ═══════════════════════════════════════════════════════════════
    # UPDATE
    # ═══════════════════════════════════════════════════════════════
    
    def update_status(
        self, 
        order: Order, 
        status: OrderStatus, 
        payment_id: str = None,
        failure_reason: str = None
    ) -> Order:
        """Update order status"""
        order.status = status
        if payment_id:
            order.payment_id = payment_id
        if failure_reason:
            order.failure_reason = failure_reason
        return order
    
    def set_payment_id(self, order: Order, payment_id: str) -> Order:
        """Set payment transaction ID"""
        order.payment_id = payment_id
        return order
    
    def set_failure_reason(self, order: Order, reason: str) -> Order:
        """Set failure reason"""
        order.failure_reason = reason
        return order
    
    # ═══════════════════════════════════════════════════════════════
    # TRANSACTION
    # ═══════════════════════════════════════════════════════════════
    
    def commit(self):
        """Commit current transaction"""
        self.db.commit()
    
    def rollback(self):
        """Rollback current transaction"""
        self.db.rollback()
    
    def refresh(self, entity):
        """Refresh entity from database"""
        self.db.refresh(entity)
        return entity
