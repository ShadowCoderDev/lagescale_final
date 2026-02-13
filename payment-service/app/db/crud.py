from sqlalchemy.orm import Session
from typing import Optional, List
from decimal import Decimal

from app.db.models import Payment, PaymentStatus


def create_payment(
    db: Session,
    transaction_id: str,
    order_id: int,
    user_id: int,
    amount: Decimal,
    status: PaymentStatus,
    message: str,
    idempotency_key: Optional[str] = None,
    original_transaction_id: Optional[str] = None
) -> Payment:
    payment = Payment(
        transaction_id=transaction_id,
        order_id=order_id,
        user_id=user_id,
        amount=amount,
        status=status,
        message=message,
        idempotency_key=idempotency_key,
        original_transaction_id=original_transaction_id
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


def create_refund(
    db: Session,
    transaction_id: str,
    original_transaction_id: str,
    order_id: int,
    user_id: int,
    amount: Decimal,
    message: str
) -> Payment:
    return create_payment(
        db=db,
        transaction_id=transaction_id,
        order_id=order_id,
        user_id=user_id,
        amount=amount,
        status=PaymentStatus.REFUNDED,
        message=message,
        original_transaction_id=original_transaction_id
    )


def get_payment_by_transaction_id(db: Session, transaction_id: str) -> Optional[Payment]:
    return db.query(Payment).filter(Payment.transaction_id == transaction_id).first()


def get_payment_by_idempotency_key(db: Session, idempotency_key: str) -> Optional[Payment]:
    return db.query(Payment).filter(Payment.idempotency_key == idempotency_key).first()


def get_successful_payment_by_order_id(db: Session, order_id: int) -> Optional[Payment]:
    return db.query(Payment).filter(
        Payment.order_id == order_id,
        Payment.status == PaymentStatus.SUCCESS
    ).first()


def get_refund_by_original_transaction(db: Session, original_transaction_id: str) -> Optional[Payment]:
    return db.query(Payment).filter(
        Payment.original_transaction_id == original_transaction_id,
        Payment.status == PaymentStatus.REFUNDED
    ).first()


def get_payments_by_order_id(db: Session, order_id: int) -> List[Payment]:
    return db.query(Payment).filter(Payment.order_id == order_id).all()
