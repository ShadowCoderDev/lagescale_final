"""
User API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_token_pair
from app.core.cookies import set_jwt_cookies, delete_jwt_cookies, set_access_token_cookie
from app.core.auth import get_current_user
from app.models.user import User
from app.schemas.user import (
    UserRegistration,
    UserLogin,
    UserProfile,
    UserUpdate,
    UserRegistrationResponse,
    UserLoginResponse,
    MessageResponse,
    TokenPair,
)

router = APIRouter()


@router.post("/register/", response_model=UserRegistrationResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegistration,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Register a new user
    
    Creates a new user account with email and password.
    JWT tokens will be set as HTTP-only cookies and also returned in response.
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Create new user
    new_user = User(
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        first_name=user_data.first_name,
        last_name=user_data.last_name,
    )
    
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Generate tokens
    tokens = create_token_pair(new_user.id, new_user.is_admin, new_user.email)
    
    # Set cookies
    set_jwt_cookies(response, tokens["access"], tokens["refresh"])
    
    # Prepare user profile response
    user_profile = UserProfile(
        id=new_user.id,
        email=new_user.email,
        first_name=new_user.first_name,
        last_name=new_user.last_name,
        full_name=new_user.get_full_name(),
        is_admin=new_user.is_admin,
        date_joined=new_user.date_joined,
        last_login=new_user.last_login,
    )
    
    return UserRegistrationResponse(
        user=user_profile,
        tokens=TokenPair(access=tokens["access"], refresh=tokens["refresh"]),
        message="Registration successful. JWT tokens are set as HTTP-only cookies and returned in response."
    )


@router.post("/login/", response_model=UserLoginResponse)
async def login(
    user_data: UserLogin,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    User login
    
    Authenticate user with email and password.
    JWT tokens will be set as HTTP-only cookies and also returned in response.
    """
    # Find user by email
    user = db.query(User).filter(User.email == user_data.email).first()
    
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is disabled"
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    db.refresh(user)
    
    # Generate tokens
    tokens = create_token_pair(user.id, user.is_admin, user.email)
    
    # Set cookies
    set_jwt_cookies(response, tokens["access"], tokens["refresh"])
    
    # Prepare user profile response
    user_profile = UserProfile(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        full_name=user.get_full_name(),
        is_admin=user.is_admin,
        date_joined=user.date_joined,
        last_login=user.last_login,
    )
    
    return UserLoginResponse(
        user=user_profile,
        tokens=TokenPair(access=tokens["access"], refresh=tokens["refresh"]),
        message="Login successful. JWT tokens are set as HTTP-only cookies and returned in response."
    )


@router.get("/profile/", response_model=UserProfile)
async def get_profile(current_user: User = Depends(get_current_user)):
    """
    Get user profile
    
    Retrieve the authenticated user's profile information.
    """
    return UserProfile(
        id=current_user.id,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        full_name=current_user.get_full_name(),
        is_admin=current_user.is_admin,
        date_joined=current_user.date_joined,
        last_login=current_user.last_login,
    )


@router.put("/profile/", response_model=UserProfile)
@router.patch("/profile/", response_model=UserProfile)
async def update_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update user profile
    
    Update the authenticated user's profile information.
    """
    # Update fields
    if user_update.first_name is not None:
        current_user.first_name = user_update.first_name
    if user_update.last_name is not None:
        current_user.last_name = user_update.last_name
    
    db.commit()
    db.refresh(current_user)
    
    return UserProfile(
        id=current_user.id,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        full_name=current_user.get_full_name(),
        is_admin=current_user.is_admin,
        date_joined=current_user.date_joined,
        last_login=current_user.last_login,
    )


@router.post("/token/refresh/", response_model=MessageResponse)
async def refresh_token(request: Request, response: Response, db: Session = Depends(get_db)):
    """
    Refresh access token
    
    Refresh access token using refresh token from HTTP-only cookie.
    New access token will be set as HTTP-only cookie.
    """
    # Get refresh token from cookie
    refresh_token = request.cookies.get("refresh_token")
    
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found in cookies"
        )
    
    # Decode refresh token
    from app.core.security import decode_token
    payload = decode_token(refresh_token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    # Check token type
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )
    
    # Get user
    user_id = payload.get("user_id")
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is disabled"
        )
    
    # Create new access token
    from app.core.security import create_access_token
    new_access_token = create_access_token({
        "user_id": user.id,
        "is_admin": user.is_admin
    })
    
    # Set new access token cookie
    set_access_token_cookie(response, new_access_token)
    
    return MessageResponse(
        message="Token refreshed successfully. New access token is set as HTTP-only cookie."
    )


@router.post("/logout/", response_model=MessageResponse)
async def logout(
    response: Response,
    current_user: User = Depends(get_current_user)
):
    """
    Logout user
    
    Logout user and clear JWT cookies.
    """
    # Delete cookies
    delete_jwt_cookies(response)
    
    return MessageResponse(
        message="Logout successful. JWT cookies have been cleared."
    )
