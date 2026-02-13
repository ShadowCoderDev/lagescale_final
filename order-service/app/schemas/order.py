from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from app.models.order import OrderStatus


class OrderItemCreate(BaseModel):
    product_id: str
    quantity: int = Field(..., gt=0)


class OrderItemResponse(BaseModel):
    id: int
    product_id: str
    product_name: str
    quantity: int
    unit_price: Decimal
    subtotal: Decimal
    
    model_config = ConfigDict(from_attributes=True)


class OrderCreate(BaseModel):
    items: List[OrderItemCreate] = Field(..., min_length=1)
    notes: Optional[str] = Field(None, max_length=1000)
    idempotency_key: Optional[str] = Field(None, max_length=64)


class OrderResponse(BaseModel):
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
    total: int
    page: int
    page_size: int
    orders: List[OrderResponse]
