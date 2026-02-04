"""Order models"""
import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Enum, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class OrderStatus(str, enum.Enum):
    """Order status"""
    PENDING = "PENDING"       # Order created, not yet processed
    RESERVED = "RESERVED"     # Stock reserved, awaiting payment (Saga)
    PROCESSING = "PROCESSING" # Payment in progress
    PAID = "PAID"             # Payment successful, stock confirmed
    FAILED = "FAILED"         # Payment or stock reservation failed
    CANCELED = "CANCELED"     # Order cancelled by user
    SHIPPED = "SHIPPED"       # Order shipped
    DELIVERED = "DELIVERED"   # Order delivered


class Order(Base):
    """Order model"""
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    total_amount = Column(Numeric(10, 2), nullable=False)
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False)
    payment_id = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    # Idempotency key to prevent duplicate orders
    idempotency_key = Column(String(64), nullable=True, unique=True, index=True)
    # Saga: store failure reason for debugging
    failure_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    """Order item model"""
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(String(255), nullable=False)
    product_name = Column(String(255), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    subtotal = Column(Numeric(10, 2), nullable=False)
    # Saga: store reservation ID for compensation
    reservation_id = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    order = relationship("Order", back_populates="items")
