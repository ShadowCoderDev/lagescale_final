"""Notification schemas"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime
from enum import Enum


class EventType(str, Enum):
    """Notification event types"""
    ORDER_CREATED = "order_created"
    PAYMENT_SUCCESS = "payment_success"
    PAYMENT_FAILED = "payment_failed"
    ORDER_CANCELED = "order_canceled"


class NotificationMessage(BaseModel):
    """Base notification message"""
    event_type: EventType
    data: dict


class OrderCreatedData(BaseModel):
    """Data for order created event"""
    email: str
    order_id: int
    total_amount: float


class PaymentSuccessData(BaseModel):
    """Data for payment success event"""
    email: str
    order_id: int
    transaction_id: str


class PaymentFailedData(BaseModel):
    """Data for payment failed event"""
    email: str
    order_id: int
    reason: str


class OrderCanceledData(BaseModel):
    """Data for order canceled event"""
    email: str
    order_id: int


class TestEmailRequest(BaseModel):
    """Request for testing email sending"""
    to_email: str = Field(..., description="Recipient email address")
    event_type: EventType = Field(..., description="Event type to simulate")
    order_id: int = Field(default=1, description="Order ID for test")
    total_amount: float = Field(default=99.99, description="Total amount for test")
    transaction_id: str = Field(default="test-txn-123", description="Transaction ID for test")
    reason: str = Field(default="Test failure reason", description="Failure reason for test")


class NotificationStatus(BaseModel):
    """Notification status response"""
    success: bool
    message: str
    event_type: Optional[str] = None


class NotificationLogResponse(BaseModel):
    """Response schema for notification logs"""
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
    """Response schema for notification statistics"""
    total: int
    sent: int
    failed: int
    pending: int
