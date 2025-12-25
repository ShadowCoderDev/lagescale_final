"""Payment API endpoints"""
import uuid
import random
import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session

from app.schemas.payment import (
    PaymentRequest,
    PaymentResponse,
    PaymentStatus
)
from app.core.config import settings
from app.db.base import get_db
from app.db import crud
from app.db.models import PaymentStatus as DBPaymentStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/payments", tags=["Payments"])


def determine_payment_outcome(amount: float) -> tuple[bool, str]:
    """
    Determine payment outcome based on amount.
    """
    amount_str = f"{amount:.2f}"
    
    if amount_str.endswith(".99"):
        return False, "Payment declined - Card rejected (test mode: .99)"
    
    if amount_str.endswith(".00"):
        return True, "Payment processed successfully"
    
    # Random outcome based on success rate
    if random.random() < settings.SUCCESS_RATE:
        return True, "Payment processed successfully"
    else:
        return False, "Payment declined by bank"


@router.post(
    "/process/",
    response_model=PaymentResponse,
    status_code=status.HTTP_200_OK,
    summary="Process payment",
    description="""
    Process a payment for an order.
    """
)
async def process_payment(payment_request: PaymentRequest, db: Session = Depends(get_db)):
    """Process a payment (simulation)"""
    logger.info(
        f"Processing payment: order_id={payment_request.order_id}, "
        f"user_id={payment_request.user_id}, amount={payment_request.amount}"
    )
    
    # Generate unique transaction ID
    transaction_id = str(uuid.uuid4())
    
    # Determine outcome
    success, message = determine_payment_outcome(payment_request.amount)
    
    # Create payment record in database
    payment_status = DBPaymentStatus.SUCCESS if success else DBPaymentStatus.FAILED
    
    payment = crud.create_payment(
        db=db,
        transaction_id=transaction_id,
        order_id=payment_request.order_id,
        user_id=payment_request.user_id,
        amount=payment_request.amount,
        status=payment_status,
        message=message
    )
    
    logger.info(
        f"Payment {transaction_id} for order {payment_request.order_id}: "
        f"{payment_status.value} - {message}"
    )
    
    return PaymentResponse(
        transaction_id=payment.transaction_id,
        order_id=payment.order_id,
        user_id=payment.user_id,
        amount=payment.amount,
        status=PaymentStatus(payment.status.value),
        message=payment.message,
        processed_at=payment.processed_at
    )


@router.get(
    "/{transaction_id}/",
    response_model=PaymentResponse,
    summary="Get payment status",
    description="Retrieve payment details by transaction ID"
)
async def get_payment(transaction_id: str, db: Session = Depends(get_db)):
    """Get payment by transaction ID"""
    payment = crud.get_payment_by_transaction_id(db, transaction_id)
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payment not found: {transaction_id}"
        )
    
    return PaymentResponse(
        transaction_id=payment.transaction_id,
        order_id=payment.order_id,
        user_id=payment.user_id,
        amount=payment.amount,
        status=PaymentStatus(payment.status.value),
        message=payment.message,
        processed_at=payment.processed_at
    )


@router.get(
    "/order/{order_id}/",
    response_model=list[PaymentResponse],
    summary="Get payments by order",
    description="Get all payment attempts for a specific order"
)
async def get_payments_by_order(order_id: int, db: Session = Depends(get_db)):
    """Get all payments for an order"""
    payments = crud.get_payments_by_order_id(db, order_id)
    
    return [
        PaymentResponse(
            transaction_id=p.transaction_id,
            order_id=p.order_id,
            user_id=p.user_id,
            amount=p.amount,
            status=PaymentStatus(p.status.value),
            message=p.message,
            processed_at=p.processed_at
        )
        for p in payments
    ]
