from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from decimal import Decimal
from enum import Enum


class PaymentStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"
    REFUNDED = "refunded"


class PaymentRequest(BaseModel):
    order_id: int
    user_id: int
    amount: Decimal = Field(..., gt=0)
    idempotency_key: Optional[str] = Field(None, max_length=64)
    
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
    transaction_id: str
    order_id: int
    user_id: int
    amount: Decimal
    status: PaymentStatus
    message: str
    processed_at: datetime
    
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
    transaction_id: str
    reason: Optional[str] = Field(None, max_length=255)
