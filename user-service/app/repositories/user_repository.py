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
        """Create a new user"""
        user = User(
            email=email,
            hashed_password=hashed_password,
            first_name=first_name,
            last_name=last_name,
            is_admin=is_admin
        )
        self.db.add(user)
        return user
    
    # ═══════════════════════════════════════════════════════════════
    # READ
    # ═══════════════════════════════════════════════════════════════
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.db.query(User).filter(User.email == email).first()
    
    def exists_by_email(self, email: str) -> bool:
        """Check if user exists by email"""
        return self.db.query(User).filter(User.email == email).first() is not None
    
    # ═══════════════════════════════════════════════════════════════
    # UPDATE
    # ═══════════════════════════════════════════════════════════════
    
    def update(self, user: User, **kwargs) -> User:
        """Update user fields"""
        for key, value in kwargs.items():
            if value is not None and hasattr(user, key):
                setattr(user, key, value)
        return user
    
    def update_last_login(self, user: User) -> User:
        """Update last login timestamp"""
        from datetime import datetime
        user.last_login = datetime.utcnow()
        return user
    
    # ═══════════════════════════════════════════════════════════════
    # TRANSACTION
    # ═══════════════════════════════════════════════════════════════
    
    def commit(self):
        """Commit current transaction"""
        self.db.commit()
    
    def rollback(self):
        """Rollback current transaction"""
        self.db.rollback()
    
    def refresh(self, entity):
        """Refresh entity from database"""
        self.db.refresh(entity)
        return entity
    
    def save(self, user: User) -> User:
        """Save user (commit and refresh)"""
        try:
            self.db.commit()
            self.db.refresh(user)
            return user
        except IntegrityError:
            self.db.rollback()
            raise
