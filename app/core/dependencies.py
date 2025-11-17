from fastapi import Depends,Header, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, OAuth2PasswordBearer,HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.user import User
from app.core.config import settings
from app.services.user_service import UserService

auth_scheme = HTTPBearer()

def get_current_user(request: Request, db=Depends(get_db), credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)):
    payload = request.state.user
    if not payload:
        raise HTTPException(401, "Unauthorized")

    service = UserService(db)
    return service.get_or_create_user(payload)
# SUPERBASE_JWT_SECRET = settings.superbase_jwt_secret
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
#     """Dependency xác thực user từ JWT"""
#     credentials_exception = HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="Could not validate credentials",
#         headers={"WWW-Authenticate": "Bearer"},
#     )

#     try:
#         payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
#         email: str = payload.get("sub")
#         if email is None:
#             raise credentials_exception
#     except JWTError:
#         raise credentials_exception

#     user = db.query(User).filter(User.email == email).first()
#     if user is None:
#         raise credentials_exception

#     return user

# auth_scheme = HTTPBearer()
# def verify_supabase_jwt(
#     credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)
# ):
#     token = credentials.credentials

#     key = SUPERBASE_JWT_SECRET

#     try:
#         payload = jwt.decode(
#             token,
#             key,
#             algorithms=["HS256"],
#             audience="authenticated",   # Supabase default
#             options={"verify_aud": True}
#         )
#         return payload

#     except JWTError as e:
#         raise HTTPException(status_code=401, detail=f"Invalid JWT: {str(e)}")