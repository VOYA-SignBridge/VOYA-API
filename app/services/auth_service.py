from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate,UserLogin
from app.core.security import hash_password, verify_password, create_access_token
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from app.core.config import settings
from app.utils.cookie_utils import set_refresh_token_cookie

def register_user(db: Session, user_in: UserCreate) -> User:
    print("Password type:", type(user_in.password), "value:", user_in.password)

    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(status_code= status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
    hashed_pw = hash_password(user_in.password)
    new_user = User(email=user_in.email, full_name= user_in.full_name, hashed_password=hashed_pw)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user



from fastapi import HTTPException, status, Response
from sqlalchemy.orm import Session
from datetime import timedelta
from app.models.user import User
from app.schemas.user import UserLogin
from app.core.security import verify_password, create_access_token
from app.utils.cookie_utils import set_refresh_token_cookie
from app.core.config import settings


def login_user(db: Session, user_in: UserLogin, response: Response):
    user = db.query(User).filter(User.email == user_in.email).first()

    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    if user.role == "disabled":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User account is disabled"
        )

    # Access token (ngắn hạn)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
    )

    # Refresh token (dài hạn)
    refresh_token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(days=settings.refresh_token_expire_days)
    )

    # Gắn refresh token vào cookie HTTP-only
    set_refresh_token_cookie(response, token=refresh_token)

    return {"access_token": access_token, "token_type": "bearer"}
