"""
User Schemas (Pydantic models)
"""
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime


class UserRegistration(BaseModel):
    """Schema for user registration"""
    email: EmailStr
    password: str = Field(..., min_length=8)
    password2: str = Field(..., min_length=8, description="Confirm password")
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    
    @field_validator('password2')
    @classmethod
    def passwords_match(cls, v, info):
        if 'password' in info.data and v != info.data['password']:
            raise ValueError("Password fields didn't match")
        return v


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str


class UserProfile(BaseModel):
    """Schema for user profile (response)"""
    id: int
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: str
    is_admin: bool
    date_joined: datetime
    last_login: Optional[datetime] = None
    
    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    """Schema for updating user profile"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    
    @field_validator('first_name', 'last_name', mode='before')
    @classmethod
    def empty_to_none(cls, v):
        # Convert empty strings to None (no update)
        if v is None:
            return None
        if isinstance(v, str):
            stripped = v.strip()
            return stripped if stripped else None
        return v


class TokenPair(BaseModel):
    """Schema for token pair"""
    access: str
    refresh: str


class UserRegistrationResponse(BaseModel):
    """Schema for registration response"""
    user: UserProfile
    tokens: TokenPair
    message: str


class UserLoginResponse(BaseModel):
    """Schema for login response"""
    user: UserProfile
    tokens: TokenPair
    message: str


class MessageResponse(BaseModel):
    """Schema for simple message response"""
    message: str
