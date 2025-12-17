from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer
from jose import jwt
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.user_service import UserService
from app.core.config import settings
import time
import requests
authentication_scheme = HTTPBearer()  # Placeholder for authentication scheme if needed
JWKS_CACHE = {"keys": None, "expired_at": 0}


def get_jwks():
    now = time.time()
    if JWKS_CACHE["keys"] and JWKS_CACHE["expired_at"] > now:
        return JWKS_CACHE["keys"]

    url = f"https://{settings.supabase_project_id}.supabase.co/auth/v1/jwks"
    print("JWKS URL =", url)

    res = requests.get(url)
    if res.status_code != 200:
        raise HTTPException(500, f"Failed to load JWKS: {res.text}")

    data = res.json()
    if "keys" not in data:
        raise HTTPException(500, f"Invalid JWKS format: {data}")

    JWKS_CACHE["keys"] = data
    JWKS_CACHE["expired_at"] = now + 3600
    return data


def verify_supabase_jwt(access_token: str):
    try:
        payload = jwt.decode(
            access_token,
            settings.supabase_jwt_secret,   # ✅ HS256 verify
            algorithms=["HS256"],
            audience="authenticated",
            issuer=f"https://{settings.supabase_project_id}.supabase.co/auth/v1",
        )
        return payload
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"JWT verification failed: {e}",
        )


def get_current_user(request: Request, db: Session = Depends(get_db), 
                     credentials: HTTPBearer = Depends(authentication_scheme)):
    auth_header = request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )

    token = auth_header.split(" ", 1)[1]

    payload = verify_supabase_jwt(token)

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