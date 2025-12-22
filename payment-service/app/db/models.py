"""Payment Database Models"""
from sqlalchemy import Column, Integer, String, Float, Enum, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
import uuid
import enum

from app.db.base import Base


class PaymentStatus(str, enum.Enum):
    """Payment status enum"""
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"


class Payment(Base):
    """Payment model for storing payment records"""
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    order_id = Column(Integer, index=True, nullable=False)
    user_id = Column(Integer, index=True, nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    message = Column(String(255), nullable=True)
    processed_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<Payment {self.transaction_id}: {self.status.value}>"
