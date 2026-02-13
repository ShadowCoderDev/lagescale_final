import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum, Text
from app.db.base import Base


class NotificationType(str, enum.Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"


class NotificationStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class NotificationLog(Base):
    __tablename__ = "notification_logs"
    
    id = Column(Integer, primary_key=True)
    notification_type = Column(Enum(NotificationType), default=NotificationType.EMAIL, nullable=False)
    recipient = Column(String(255), nullable=False)
    subject = Column(String(255))
    content = Column(Text, nullable=True)
    event_type = Column(String(50))
    order_id = Column(Integer, index=True)
    user_id = Column(Integer, index=True)
    status = Column(Enum(NotificationStatus), default=NotificationStatus.PENDING)
    error_message = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    sent_at = Column(DateTime)

