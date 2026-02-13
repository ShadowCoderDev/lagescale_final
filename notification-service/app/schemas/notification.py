from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime
from enum import Enum


class EventType(str, Enum):
    ORDER_CREATED = "order_created"
    PAYMENT_SUCCESS = "payment_success"
    PAYMENT_FAILED = "payment_failed"
    ORDER_CANCELED = "order_canceled"


class NotificationMessage(BaseModel):
    event_type: EventType
    data: dict


class OrderCreatedData(BaseModel):
    email: str
    order_id: int
    total_amount: float


class PaymentSuccessData(BaseModel):
    email: str
    order_id: int
    transaction_id: str


class PaymentFailedData(BaseModel):
    email: str
    order_id: int
    reason: str


class OrderCanceledData(BaseModel):
    email: str
    order_id: int


class TestEmailRequest(BaseModel):
    to_email: str = Field(...)
    event_type: EventType = Field(...)
    order_id: int = Field(default=1)
    total_amount: float = Field(default=99.99)
    transaction_id: str = Field(default="test-txn-123")
    reason: str = Field(default="Test failure reason")


class NotificationStatus(BaseModel):
    success: bool
    message: str
    event_type: Optional[str] = None


class NotificationLogResponse(BaseModel):
    id: int
    notification_type: str
    recipient: str
    subject: Optional[str] = None
    event_type: Optional[str] = None
    order_id: Optional[int] = None
    user_id: Optional[int] = None
    status: str
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class NotificationStatsResponse(BaseModel):
    total: int
    sent: int
    failed: int
    pending: int
