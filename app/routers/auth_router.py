from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas.user import UserCreate, UserLogin, UserOut
from app.services.auth_service import AuthService
from app.db.database import get_db
from fastapi import Response, Request
from app.utils.cookie_utils import get_refresh_token_cookie, clear_refresh_token_cookie
from app.core.security import create_access_token, decode_token
from app.utils.cookie_utils import set_refresh_token_cookie
from datetime import timedelta
from app.core.config import settings
from app.models.user import User
from app.core.dependencies import  get_current_user
from fastapi.security import OAuth2PasswordRequestForm
from app.services.user_service import UserService
router= APIRouter(prefix="/auth", tags=["AUTHENTICATION SERVICE"])



@router.get("/me")
def get_me(user = Depends(get_current_user)):
    return {
        "id": user.id,
        "supabase_id": user.supabase_id,
        "email": user.email,
        "full_name": user.full_name,
    }

