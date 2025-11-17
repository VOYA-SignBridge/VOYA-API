from datetime import timedelta
from fastapi import HTTPException, Response
from sqlalchemy.orm import Session
from app.repositories.user_repo import UserRepository
from app.core.security import hash_password, verify_password, create_access_token
from app.core.config import settings
from app.utils.cookie_utils import set_refresh_token_cookie


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = UserRepository(db)

    def register(self, user_in):
        existing_user = self.repo.get_user_by_email(user_in.email)
        if existing_user:
            raise HTTPException(400, "Email already registered")

        hashed_pw = hash_password(user_in.password)
        return self.repo.create_user(
            email=user_in.email,
            password_hash=hashed_pw,
            full_name=user_in.full_name
        )

    def login(self, user_in, response: Response):
        user = self.repo.get_user_by_email(user_in.email)
        if not user or not verify_password(user_in.password, user.hashed_password):
            raise HTTPException(401, "Invalid credentials")

        if user.role == "disabled":
            raise HTTPException(403, "User disabled")

        access_token = create_access_token(
            {"sub": user.email},
            timedelta(minutes=settings.access_token_expire_minutes)
        )

        refresh_token = create_access_token(
            {"sub": user.email},
            timedelta(days=settings.refresh_token_expire_days)
        )
        set_refresh_token_cookie(response, refresh_token)

        return {"access_token": access_token, "token_type": "bearer"}
