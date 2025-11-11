from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas.user import UserCreate, UserLogin, UserOut
from app.services.auth_service import register_user, login_user
from app.db.database import get_db
from fastapi import Response, Request
from app.utils.cookie_utils import get_refresh_token_cookie, clear_refresh_token_cookie
from app.core.security import create_access_token, decode_token
from app.utils.cookie_utils import set_refresh_token_cookie
from datetime import timedelta
from app.core.config import settings
from app.models.user import User
from app.core.dependencies import get_current_user
from fastapi.security import OAuth2PasswordRequestForm

router= APIRouter(prefix="/auth", tags=["AUTHENTICATION SERVICE"])



@router.get("/me", summary="Thông tin người dùng hiện tại")
def read_current_user(current_user: User = Depends(get_current_user)):
    return {
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role
    }

@router.post("/register", response_model=UserOut)
def register(user_in: UserCreate, db: Session= Depends(get_db)):
    return register_user(db, user_in)

# @router.post("/login")
# def login(
#     user_in: UserLogin,
#     response: Response,
#     db: Session = Depends(get_db)
# ):
#     return login_user(db, user_in, response)

@router.post("/login")
def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user_in = UserLogin(email=form_data.username, password=form_data.password)
    return login_user(db, user_in, response)



@router.post("/refresh", summary="Cấp lại access token mới")
def refresh_access_token(request: Request, response: Response, db: Session = Depends(get_db)):
    refresh_token = get_refresh_token_cookie(request)
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing refresh token")
    email = decode_token(refresh_token)
    if not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    new_access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
    )
    new_refresh_token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(days=settings.refresh_token_expire_days)
    )
    set_refresh_token_cookie(response, new_refresh_token)
    return {"access_token": new_access_token, "token_type": "bearer"}
