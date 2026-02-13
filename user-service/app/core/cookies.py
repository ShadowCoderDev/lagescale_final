from fastapi import Response
from app.core.config import settings


def set_jwt_cookies(response: Response, access_token: str, refresh_token: str):
    response.set_cookie(
        key=settings.ACCESS_COOKIE_NAME,
        value=access_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        domain=settings.COOKIE_DOMAIN,
    )
    
    response.set_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        domain=settings.COOKIE_DOMAIN,
    )


def set_access_token_cookie(response: Response, access_token: str):
    response.set_cookie(
        key=settings.ACCESS_COOKIE_NAME,
        value=access_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        domain=settings.COOKIE_DOMAIN,
    )


def delete_jwt_cookies(response: Response):
    response.delete_cookie(
        key=settings.ACCESS_COOKIE_NAME,
        domain=settings.COOKIE_DOMAIN,
    )
    response.delete_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        domain=settings.COOKIE_DOMAIN,
    )
