import time

from fastapi import HTTPException, Request
from fastapi.security.utils import get_authorization_scheme_param
import requests
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings
from jose import jwt

JWKS_CACHE= {"keys": None, "expired_at": 0}
PUBLIC_PATHS = {
    "/docs",
    "/redoc",
    "/openapi.json"
}

def get_jwks():
    now = time.time()
    if JWKS_CACHE["keys"] and JWKS_CACHE["expired_at"] > now:
        return JWKS_CACHE["keys"]

    url = f"https://{settings.supabase_project_id}.supabase.co/auth/v1/jwks"
    print("JWKS URL =", url)

    res = requests.get(url)

    # ✅ kiểm tra response hợp lệ
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
        raise HTTPException(status_code=401, detail=f"JWT verification failed: {e}")


    
class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # ✅ skip authentication cho các route public
        if path in PUBLIC_PATHS or path.startswith("/static"):
            return await call_next(request)

        # ✅ lấy Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

        token = auth_header.split(" ")[1]

        try:
            payload = verify_supabase_jwt(token)
            request.state.user = payload
        except Exception as e:
            raise HTTPException(status_code=401, detail=str(e))

        return await call_next(request)
