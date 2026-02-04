"""Order schemas"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from app.models.order import OrderStatus


class OrderItemCreate(BaseModel):
    """Create order item"""
    product_id: str
    quantity: int = Field(..., gt=0)


class OrderItemResponse(BaseModel):
    """Order item response"""
    id: int
    product_id: str
    product_name: str
    quantity: int
    unit_price: Decimal
    subtotal: Decimal
    
    model_config = ConfigDict(from_attributes=True)


class OrderCreate(BaseModel):
    """Create order"""
    items: List[OrderItemCreate] = Field(..., min_length=1)
    notes: Optional[str] = Field(None, max_length=1000)
    # Idempotency key to prevent duplicate orders (optional but recommended)
    idempotency_key: Optional[str] = Field(None, max_length=64, description="Unique key to prevent duplicate orders")


class OrderResponse(BaseModel):
    """Order response"""
    id: int
    user_id: int
    total_amount: Decimal
    status: OrderStatus
    payment_id: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemResponse]
    
    model_config = ConfigDict(from_attributes=True)


class OrderListResponse(BaseModel):
    """Paginated order list"""
    total: int
    page: int
    page_size: int
    orders: List[OrderResponse]
