import logging
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session

from app.schemas.payment import (
    PaymentRequest,
    PaymentResponse,
    PaymentStatus,
    RefundRequest
)
from app.db.base import get_db
from app.services.payment_service import PaymentService, PaymentServiceError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/payments", tags=["Payments"])


# ═══════════════════════════════════════════════════════════════════════════════
# PAYMENT PROCESSING
# ═══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/process/",
    response_model=PaymentResponse,
    status_code=status.HTTP_200_OK,
)
async def process_payment(payment_request: PaymentRequest, db: Session = Depends(get_db)):
    service = PaymentService(db)
    
    try:
        result = service.process_payment(payment_request)
        return PaymentResponse(
            transaction_id=result["transaction_id"],
            order_id=result["order_id"],
            user_id=result["user_id"],
            amount=result["amount"],
            status=PaymentStatus(result["status"]),
            message=result["message"],
            processed_at=result["processed_at"]
        )
    except PaymentServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


# ═══════════════════════════════════════════════════════════════════════════════
# REFUND
# ═══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/refund/",
    response_model=PaymentResponse,
    status_code=status.HTTP_200_OK,
)
async def refund_payment(refund_request: RefundRequest, db: Session = Depends(get_db)):
    service = PaymentService(db)
    
    try:
        result = service.refund_payment(refund_request)
        return PaymentResponse(
            transaction_id=result["transaction_id"],
            order_id=result["order_id"],
            user_id=result["user_id"],
            amount=result["amount"],
            status=PaymentStatus(result["status"]),
            message=result["message"],
            processed_at=result["processed_at"]
        )
    except PaymentServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


# ═══════════════════════════════════════════════════════════════════════════════
# QUERIES
# ═══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/{transaction_id}/",
    response_model=PaymentResponse,
)
async def get_payment(transaction_id: str, db: Session = Depends(get_db)):
    service = PaymentService(db)
    
    try:
        result = service.get_payment(transaction_id)
        return PaymentResponse(
            transaction_id=result["transaction_id"],
            order_id=result["order_id"],
            user_id=result["user_id"],
            amount=result["amount"],
            status=PaymentStatus(result["status"]),
            message=result["message"],
            processed_at=result["processed_at"]
        )
    except PaymentServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get(
    "/order/{order_id}/",
    response_model=list[PaymentResponse],
)
async def get_payments_by_order(order_id: int, db: Session = Depends(get_db)):
    service = PaymentService(db)
    
    results = service.get_order_payments(order_id)
    
    return [
        PaymentResponse(
            transaction_id=r["transaction_id"],
            order_id=r["order_id"],
            user_id=r["user_id"],
            amount=r["amount"],
            status=PaymentStatus(r["status"]),
            message=r["message"],
            processed_at=r["processed_at"]
        )
        for r in results
    ]
