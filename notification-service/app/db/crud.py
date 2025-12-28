"""CRUD"""
from datetime import datetime
from sqlalchemy.orm import Session
from app.db.models import NotificationLog, NotificationType, NotificationStatus


def create_notification_log(db, notification_type, recipient, subject=None, content=None, 
                           event_type=None, order_id=None, user_id=None, status=NotificationStatus.PENDING):
    """Create a notification log entry"""
    log = NotificationLog(
        notification_type=notification_type,  # اصلاح شد - حالا ذخیره می‌شود
        recipient=recipient,
        subject=subject,
        content=content,  # اصلاح شد - حالا ذخیره می‌شود
        event_type=event_type,
        order_id=order_id,
        user_id=user_id,
        status=status
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def update_notification_status(db, log_id, status, error_message=None):
    log = db.query(NotificationLog).filter(NotificationLog.id == log_id).first()
    if log:
        log.status = status
        if status == NotificationStatus.SENT:
            log.sent_at = datetime.utcnow()
        if error_message:
            log.error_message = error_message
        db.commit()
    return log


def get_recent_notifications(db, limit=50):
    return db.query(NotificationLog).order_by(NotificationLog.created_at.desc()).limit(limit).all()


def get_notifications_by_order(db, order_id):
    return db.query(NotificationLog).filter(NotificationLog.order_id == order_id).all()


def count_notifications(db):
    return db.query(NotificationLog).count()


def count_notifications_by_status(db, status):
    return db.query(NotificationLog).filter(NotificationLog.status == status).count()

