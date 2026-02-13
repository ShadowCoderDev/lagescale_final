import uuid
import random
import logging
from decimal import Decimal
from typing import Optional
from sqlalchemy.orm import Session

from app.db import crud
from app.db.models import Payment, PaymentStatus as DBPaymentStatus
from app.core.config import settings
from app.schemas.payment import PaymentRequest, RefundRequest

logger = logging.getLogger(__name__)


class PaymentServiceError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class PaymentService:
    
    def __init__(self, db: Session):
        self.db = db
    
    # ═══════════════════════════════════════════════════════════════
    # PRIVATE METHODS
    # ═══════════════════════════════════════════════════════════════
    
    @staticmethod
    def _determine_payment_outcome(amount: Decimal) -> tuple[bool, str]:
        """Test mode: .99 always fails, .00 always succeeds, else random."""
        amount_str = f"{float(amount):.2f}"
        
        if amount_str.endswith(".99"):
            return False, "Payment declined - Card rejected (test mode: .99)"
        
        if amount_str.endswith(".00"):
            return True, "Payment processed successfully"
        
        if random.random() < settings.SUCCESS_RATE:
            return True, "Payment processed successfully"
        else:
            return False, "Payment declined by bank"
    
    def _payment_to_response(self, payment: Payment) -> dict:
        return {
            "transaction_id": payment.transaction_id,
            "order_id": payment.order_id,
            "user_id": payment.user_id,
            "amount": payment.amount,
            "status": payment.status.value,
            "message": payment.message,
            "processed_at": payment.processed_at
        }
    
    # ═══════════════════════════════════════════════════════════════
    # PAYMENT PROCESSING
    # ═══════════════════════════════════════════════════════════════
    
    def process_payment(self, request: PaymentRequest) -> dict:
        logger.info(
            f"Processing payment: order_id={request.order_id}, "
            f"user_id={request.user_id}, amount={request.amount}"
        )
        
        if request.idempotency_key:
            existing = crud.get_payment_by_idempotency_key(self.db, request.idempotency_key)
            if existing:
                logger.info(f"Idempotency key found, returning existing payment {existing.transaction_id}")
                return self._payment_to_response(existing)
        
        existing_successful = crud.get_successful_payment_by_order_id(self.db, request.order_id)
        if existing_successful:
            raise PaymentServiceError(
                f"Order {request.order_id} already has a successful payment"
            )
        
        transaction_id = str(uuid.uuid4())
        
        success, message = self._determine_payment_outcome(request.amount)
        
        # Create payment record
        payment_status = DBPaymentStatus.SUCCESS if success else DBPaymentStatus.FAILED
        
        payment = crud.create_payment(
            db=self.db,
            transaction_id=transaction_id,
            order_id=request.order_id,
            user_id=request.user_id,
            amount=request.amount,
            status=payment_status,
            message=message,
            idempotency_key=request.idempotency_key
        )
        
        logger.info(
            f"Payment {transaction_id} for order {request.order_id}: "
            f"{payment_status.value} - {message}"
        )
        
        return self._payment_to_response(payment)
    
    # ═══════════════════════════════════════════════════════════════
    # REFUND
    # ═══════════════════════════════════════════════════════════════
    
    def refund_payment(self, request: RefundRequest) -> dict:
        """Refund a successful payment"""
        # Get original payment
        original_payment = crud.get_payment_by_transaction_id(self.db, request.transaction_id)
        
        if not original_payment:
            raise PaymentServiceError(
                f"Payment not found: {request.transaction_id}",
                404
            )
        
        if original_payment.status != DBPaymentStatus.SUCCESS:
            raise PaymentServiceError(
                f"Cannot refund payment with status: {original_payment.status.value}"
            )
        
        # Check if already refunded
        existing_refund = crud.get_refund_by_original_transaction(self.db, request.transaction_id)
        if existing_refund:
            raise PaymentServiceError(
                f"Payment already refunded: {existing_refund.transaction_id}"
            )
        
        # Process refund
        refund_transaction_id = str(uuid.uuid4())
        
        refund = crud.create_refund(
            db=self.db,
            transaction_id=refund_transaction_id,
            original_transaction_id=request.transaction_id,
            order_id=original_payment.order_id,
            user_id=original_payment.user_id,
            amount=original_payment.amount,
            message=f"Refund for {request.transaction_id}: {request.reason or 'No reason provided'}"
        )
        
        logger.info(f"Payment {request.transaction_id} refunded: {refund_transaction_id}")
        
        return self._payment_to_response(refund)
    
    # ═══════════════════════════════════════════════════════════════
    # QUERIES
    # ═══════════════════════════════════════════════════════════════
    
    def get_payment(self, transaction_id: str) -> dict:
        payment = crud.get_payment_by_transaction_id(self.db, transaction_id)
        
        if not payment:
            raise PaymentServiceError(f"Payment not found: {transaction_id}", 404)
        
        return self._payment_to_response(payment)
    
    def get_order_payments(self, order_id: int) -> list:
        payments = crud.get_payments_by_order_id(self.db, order_id)
        return [self._payment_to_response(p) for p in payments]
