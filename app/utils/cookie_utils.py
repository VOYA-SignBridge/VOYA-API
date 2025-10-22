from fastapi import Response, Request
from typing import Optional

REFRESH_TOKEN_NAME = "refresh_token"


def set_refresh_token_cookie(
    response: Response,
    token: str,
    max_age_seconds: int = 7 * 24 * 3600,
    secure: bool = True
):
    
    response.set_cookie(
        key=REFRESH_TOKEN_NAME,
        value=token,
        httponly=True,
        secure=secure,
        samesite="None" if secure else "Lax",
        max_age=max_age_seconds,
        path="/"
    )


def get_refresh_token_cookie(request: Request) -> Optional[str]:
   
    return request.cookies.get(REFRESH_TOKEN_NAME)


def clear_refresh_token_cookie(response: Response):
   
    response.delete_cookie(
        key=REFRESH_TOKEN_NAME,
        path="/"
    )
