"""
User Service - Business Logic Layer
Handles all business logic for user operations
"""
import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.core.security import hash_password, verify_password, create_token_pair
from app.schemas.user import UserRegistration, UserLogin, UserUpdate

logger = logging.getLogger(__name__)


class UserServiceError(Exception):
    """Base exception for user service errors"""
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class UserService:
    """
    User Service - Business Logic Layer
    
    Responsibilities:
    - Validate business rules
    - Handle authentication
    - Manage user operations
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = UserRepository(db)
    
    # ═══════════════════════════════════════════════════════════════
    # AUTHENTICATION
    # ═══════════════════════════════════════════════════════════════
    
    def register(self, data: UserRegistration) -> tuple[User, Dict[str, str]]:
        """
        Register a new user
        Returns (user, tokens)
        """
        if self.repository.exists_by_email(data.email):
            raise UserServiceError("کاربری با این ایمیل قبلاً ثبت‌نام کرده است")
        
        try:
            user = self.repository.create(
                email=data.email,
                hashed_password=hash_password(data.password),
                first_name=data.first_name,
                last_name=data.last_name
            )
            self.repository.save(user)
        except IntegrityError:
            raise UserServiceError("کاربری با این ایمیل قبلاً ثبت‌نام کرده است")
        
        tokens = create_token_pair(user.id, user.is_admin, user.email)
        
        logger.info(f"User registered: {user.email}")
        return user, tokens
    
    def login(self, data: UserLogin) -> tuple[User, Dict[str, str]]:
        user = self.repository.get_by_email(data.email)
        
        if not user or not verify_password(data.password, user.hashed_password):
            raise UserServiceError("ایمیل یا رمز عبور اشتباه است")
        
        if not user.is_active:
            raise UserServiceError("حساب کاربری غیرفعال است")
        
        self.repository.update_last_login(user)
        self.repository.save(user)
        
        tokens = create_token_pair(user.id, user.is_admin, user.email)
        
        logger.info(f"User logged in: {user.email}")
        return user, tokens
    
    def refresh_token(self, user_id: int) -> Optional[str]:
        user = self.repository.get_by_id(user_id)
        
        if not user:
            raise UserServiceError("کاربر یافت نشد", 404)
        
        if not user.is_active:
            raise UserServiceError("حساب کاربری غیرفعال است")
        
        from app.core.security import create_access_token
        return create_access_token({
            "user_id": user.id,
            "is_admin": user.is_admin,
            "email": user.email
        })
    
    def get_profile(self, user_id: int) -> Optional[User]:
        return self.repository.get_by_id(user_id)
    
    def update_profile(self, user: User, data: UserUpdate) -> User:
        self.repository.update(
            user,
            first_name=data.first_name,
            last_name=data.last_name
        )
        return self.repository.save(user)
