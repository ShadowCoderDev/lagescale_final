"""Payment schemas"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class PaymentStatus(str, Enum):
    """Payment status enum"""
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"


class PaymentRequest(BaseModel):
    """Payment request schema"""
    order_id: int = Field(..., description="Order ID")
    user_id: int = Field(..., description="User ID")
    amount: float = Field(..., gt=0, description="Payment amount (must be positive)")
    
    class Config:
        schema_extra = {
            "example": {
                "order_id": 1,
                "user_id": 1,
                "amount": 99.99
            }
        }


class PaymentResponse(BaseModel):
    """Payment response schema"""
    transaction_id: str = Field(..., description="Unique transaction ID")
    order_id: int = Field(..., description="Order ID")
    user_id: int = Field(..., description="User ID")
    amount: float = Field(..., description="Payment amount")
    status: PaymentStatus = Field(..., description="Payment status")
    message: str = Field(..., description="Status message")
    processed_at: datetime = Field(..., description="Processing timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "transaction_id": "550e8400-e29b-41d4-a716-446655440000",
                "order_id": 1,
                "user_id": 1,
                "amount": 99.99,
                "status": "success",
                "message": "Payment processed successfully",
                "processed_at": "2025-12-18T10:30:00"
            }
        }
