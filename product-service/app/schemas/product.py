"""Product Schemas"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal


class ProductBase(BaseModel):
    """Base product schema"""
    name: str = Field(..., max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    price: Decimal = Field(..., ge=0, decimal_places=2)
    stockQuantity: int = Field(..., ge=0)
    category: str = Field(..., max_length=100)
    sku: str = Field(..., max_length=100)
    isActive: bool = True


class ProductCreate(ProductBase):
    """Schema for creating product"""
    pass


class ProductUpdate(BaseModel):
    """Schema for updating product"""
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    price: Optional[Decimal] = Field(None, ge=0)
    stockQuantity: Optional[int] = Field(None, ge=0)
    category: Optional[str] = Field(None, max_length=100)
    sku: Optional[str] = Field(None, max_length=100)
    isActive: Optional[bool] = None


class ProductResponse(ProductBase):
    """Schema for product response"""
    id: str
    createdAt: datetime
    updatedAt: datetime
    
    model_config = {"from_attributes": True}


class ProductListResponse(BaseModel):
    """Simplified product for list views"""
    id: str
    name: str
    price: Decimal
    stockQuantity: int
    category: str
    sku: str
    isActive: bool


class ProductStockResponse(BaseModel):
    """Stock information response"""
    product_id: str
    stock_quantity: int
    in_stock: bool
    available: bool


class PaginatedResponse(BaseModel):
    """Paginated response"""
    count: int
    next: Optional[str] = None
    previous: Optional[str] = None
    results: list
