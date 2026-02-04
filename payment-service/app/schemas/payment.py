"""Payment schemas"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from decimal import Decimal
from enum import Enum


class PaymentStatus(str, Enum):
    """Payment status enum"""
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"
    REFUNDED = "refunded"  # اضافه شد برای پشتیبانی از refund


class PaymentRequest(BaseModel):
    """Payment request schema"""
    order_id: int = Field(..., description="Order ID")
    user_id: int = Field(..., description="User ID")
    amount: Decimal = Field(..., gt=0, description="Payment amount (must be positive)")
    # Idempotency key برای جلوگیری از پرداخت تکراری
    idempotency_key: Optional[str] = Field(None, max_length=64, description="Unique key to prevent duplicate payments")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "order_id": 1,
                "user_id": 1,
                "amount": "99.99",
                "idempotency_key": "pay-order-1-uuid"
            }
        }
    )


class PaymentResponse(BaseModel):
    """Payment response schema"""
    transaction_id: str = Field(..., description="Unique transaction ID")
    order_id: int = Field(..., description="Order ID")
    user_id: int = Field(..., description="User ID")
    amount: Decimal = Field(..., description="Payment amount")
    status: PaymentStatus = Field(..., description="Payment status")
    message: str = Field(..., description="Status message")
    processed_at: datetime = Field(..., description="Processing timestamp")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "transaction_id": "550e8400-e29b-41d4-a716-446655440000",
                "order_id": 1,
                "user_id": 1,
                "amount": "99.99",
                "status": "success",
                "message": "Payment processed successfully",
                "processed_at": "2025-12-18T10:30:00"
            }
        }
    )


class RefundRequest(BaseModel):
    """Refund request schema"""
    transaction_id: str = Field(..., description="Original transaction ID to refund")
    reason: Optional[str] = Field(None, max_length=255, description="Reason for refund")
