"""
Order API - Controller Layer
Handles HTTP requests/responses only
Business logic is in service layer
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.order import Order, OrderStatus
from app.schemas.order import (
    OrderCreate,
    OrderResponse,
    OrderListResponse
)
from app.services.order_service import OrderService, OrderServiceError

logger = logging.getLogger(__name__)
router = APIRouter()


# ═══════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def order_to_response(order: Order) -> dict:
    """Convert Order model to response dict"""
    return {
        "id": order.id,
        "user_id": order.user_id,
        "total_amount": order.total_amount,
        "status": order.status,
        "payment_id": order.payment_id,
        "notes": order.notes,
        "created_at": order.created_at,
        "updated_at": order.updated_at,
        "items": [
            {
                "id": item.id,
                "product_id": item.product_id,
                "product_name": item.product_name,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "subtotal": item.subtotal,
            }
            for item in order.items
        ]
    }


def get_order_service(db: Session = Depends(get_db)) -> OrderService:
    """Dependency injection for OrderService"""
    return OrderService(db)


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def checkout(
    order_data: OrderCreate,
    current_user: dict = Depends(get_current_user),
    service: OrderService = Depends(get_order_service)
):
    """
    Create order and process payment (Checkout)
    
    - Validates products
    - Reserves stock
    - Processes payment
    - Confirms stock deduction
    """
    try:
        order = service.checkout(
            order_data=order_data,
            user_id=current_user.get("user_id"),
            user_email=current_user.get("email")
        )
        return order_to_response(order)
    
    except OrderServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/", response_model=OrderListResponse)
def list_orders(
    status_filter: Optional[OrderStatus] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    service: OrderService = Depends(get_order_service)
):
    """List user orders with pagination"""
    orders, total = service.list_orders(
        user_id=current_user.get("user_id"),
        status_filter=status_filter,
        page=page,
        page_size=page_size
    )
    
    return OrderListResponse(
        total=total,
        page=page,
        page_size=page_size,
        orders=[order_to_response(o) for o in orders]
    )


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int,
    current_user: dict = Depends(get_current_user),
    service: OrderService = Depends(get_order_service)
):
    """Get order by ID"""
    order = service.get_order(
        order_id=order_id,
        user_id=current_user.get("user_id")
    )
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="سفارش یافت نشد"
        )
    
    return order_to_response(order)


@router.post("/{order_id}/cancel")
def cancel_order(
    order_id: int,
    current_user: dict = Depends(get_current_user),
    service: OrderService = Depends(get_order_service)
):
    """Cancel an order"""
    try:
        order = service.cancel_order(
            order_id=order_id,
            user_id=current_user.get("user_id")
        )
        return {
            "message": "سفارش با موفقیت لغو شد",
            "order_id": order.id,
            "status": order.status.value
        }
    
    except OrderServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
