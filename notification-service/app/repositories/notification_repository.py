from typing import Optional, List
from sqlalchemy.orm import Session

from app.db import crud
from app.db.models import NotificationLog, NotificationType, NotificationStatus


class NotificationRepository:
    
    def __init__(self, db: Session):
        self.db = db
    

    def create_log(
        self,
        notification_type: NotificationType,
        recipient: str,
        subject: str,
        content: str,
        event_type: Optional[str] = None,
        order_id: Optional[int] = None,
        user_id: Optional[int] = None,
        status: NotificationStatus = NotificationStatus.PENDING
    ) -> NotificationLog:
        return crud.create_notification_log(
            db=self.db,
            notification_type=notification_type,
            recipient=recipient,
            subject=subject,
            content=content,
            event_type=event_type,
            order_id=order_id,
            user_id=user_id,
            status=status
        )
    
    def get_by_id(self, notification_id: int) -> Optional[NotificationLog]:
        return crud.get_notification_by_id(self.db, notification_id)
    
    def list_by_order(self, order_id: int) -> List[NotificationLog]:
        return crud.get_notifications_by_order(self.db, order_id)
    
    def list_by_user(self, user_id: int) -> List[NotificationLog]:
        return crud.get_notifications_by_user(self.db, user_id)
    
    def update_status(
        self,
        notification_id: int,
        status: NotificationStatus,
        error_message: Optional[str] = None
    ) -> Optional[NotificationLog]:
        return crud.update_notification_status(
            self.db, notification_id, status, error_message
        )
    
    def mark_sent(self, notification_id: int) -> Optional[NotificationLog]:
        return self.update_status(notification_id, NotificationStatus.SENT)
    
    def mark_failed(self, notification_id: int, error: str) -> Optional[NotificationLog]:
        return self.update_status(notification_id, NotificationStatus.FAILED, error)
