from sqlalchemy import Column, Integer, String, Numeric, Enum, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
import uuid
import enum

from app.db.base import Base


class PaymentStatus(str, enum.Enum):
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"
    REFUNDED = "refunded"


class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    order_id = Column(Integer, index=True, nullable=False)
    user_id = Column(Integer, index=True, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    message = Column(String(255), nullable=True)
    idempotency_key = Column(String(64), unique=True, nullable=True, index=True)
    original_transaction_id = Column(String(36), nullable=True, index=True)
    processed_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<Payment {self.transaction_id}: {self.status.value}>"
