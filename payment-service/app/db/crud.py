"""Payment CRUD operations"""
from sqlalchemy.orm import Session
from typing import Optional, List

from app.db.models import Payment, PaymentStatus


def create_payment(
    db: Session,
    transaction_id: str,
    order_id: int,
    user_id: int,
    amount: float,
    status: PaymentStatus,
    message: str
) -> Payment:
    """Create a new payment record"""
    payment = Payment(
        transaction_id=transaction_id,
        order_id=order_id,
        user_id=user_id,
        amount=amount,
        status=status,
        message=message
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


def get_payment_by_transaction_id(db: Session, transaction_id: str) -> Optional[Payment]:
    """Get payment by transaction ID"""
    return db.query(Payment).filter(Payment.transaction_id == transaction_id).first()


def get_payments_by_order_id(db: Session, order_id: int) -> List[Payment]:
    """Get all payments for an order"""
    return db.query(Payment).filter(Payment.order_id == order_id).all()
