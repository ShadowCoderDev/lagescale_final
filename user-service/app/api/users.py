"""
User API - Controller Layer

Handles HTTP requests/responses only.
All business logic is delegated to UserService.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.cookies import set_jwt_cookies, delete_jwt_cookies, set_access_token_cookie
from app.core.auth import get_current_user
from app.models.user import User
from app.services.user_service import UserService, UserServiceError
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


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def _build_user_profile(user: User) -> UserProfile:
    """Build UserProfile from User model"""
    return UserProfile(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        full_name=user.get_full_name(),
        is_admin=user.is_admin,
        date_joined=user.date_joined,
        last_login=user.last_login,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# AUTHENTICATION ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

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
    service = UserService(db)
    
    try:
        user, tokens = service.register(user_data)
    except UserServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    
    # Set cookies
    set_jwt_cookies(response, tokens["access"], tokens["refresh"])
    
    return UserRegistrationResponse(
        user=_build_user_profile(user),
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
    service = UserService(db)
    
    try:
        user, tokens = service.login(user_data)
    except UserServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    
    # Set cookies
    set_jwt_cookies(response, tokens["access"], tokens["refresh"])
    
    return UserLoginResponse(
        user=_build_user_profile(user),
        tokens=TokenPair(access=tokens["access"], refresh=tokens["refresh"]),
        message="Login successful. JWT tokens are set as HTTP-only cookies and returned in response."
    )


@router.get("/profile/", response_model=UserProfile)
async def get_profile(current_user: User = Depends(get_current_user)):
    """
    Get user profile
    
    Retrieve the authenticated user's profile information.
    """
    return _build_user_profile(current_user)


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
    service = UserService(db)
    
    try:
        user = service.update_profile(current_user, user_update)
    except UserServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    
    return _build_user_profile(user)


@router.post("/token/refresh/", response_model=MessageResponse)
async def refresh_token(request: Request, response: Response, db: Session = Depends(get_db)):
    """
    Refresh access token
    
    Refresh access token using refresh token from HTTP-only cookie.
    New access token will be set as HTTP-only cookie.
    """
    # Get refresh token from cookie
    refresh_token_value = request.cookies.get("refresh_token")
    
    if not refresh_token_value:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found in cookies"
        )
    
    # Decode refresh token
    from app.core.security import decode_token
    payload = decode_token(refresh_token_value)
    
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
    
    # Refresh token via service
    user_id = payload.get("user_id")
    service = UserService(db)
    
    try:
        new_access_token = service.refresh_token(user_id)
    except UserServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    
    # Set new access token cookie
    set_access_token_cookie(response, new_access_token)
    
    return MessageResponse(
        message="Token refreshed successfully. New access token is set as HTTP-only cookie."
    )


# ═══════════════════════════════════════════════════════════════════════════════
# LOGOUT
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/logout/", response_model=MessageResponse)
async def logout(
    response: Response,
    current_user: User = Depends(get_current_user)
):
    """
    Logout user
    
    Logout user and clear JWT cookies.
    """
    delete_jwt_cookies(response)
    
    return MessageResponse(
        message="Logout successful. JWT cookies have been cleared."
    )
