"""
User Repository - Data Access Layer
Handles all database operations for users
"""
import logging
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.user import User

logger = logging.getLogger(__name__)


class UserRepository:
    """Repository for User database operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ═══════════════════════════════════════════════════════════════
    # CREATE
    # ═══════════════════════════════════════════════════════════════
    
    def create(
        self,
        email: str,
        hashed_password: str,
        first_name: str = None,
        last_name: str = None,
        is_admin: bool = False
    ) -> User:
        user = User(
            email=email,
            hashed_password=hashed_password,
            first_name=first_name,
            last_name=last_name,
            is_admin=is_admin
        )
        self.db.add(user)
        return user
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()
    
    def exists_by_email(self, email: str) -> bool:
        return self.db.query(User).filter(User.email == email).first() is not None
    
    def update(self, user: User, **kwargs) -> User:
        for key, value in kwargs.items():
            if value is not None and hasattr(user, key):
                setattr(user, key, value)
        return user
    
    def update_last_login(self, user: User) -> User:
        from datetime import datetime
        user.last_login = datetime.utcnow()
        return user
    
    def commit(self):
        self.db.commit()
    
    def rollback(self):
        self.db.rollback()
    
    def refresh(self, entity):
        self.db.refresh(entity)
        return entity
    
    def save(self, user: User) -> User:
        try:
            self.db.commit()
            self.db.refresh(user)
            return user
        except IntegrityError:
            self.db.rollback()
            raise
