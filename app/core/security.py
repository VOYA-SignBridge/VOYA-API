from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings
import hashlib


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def _normalize_password(password) -> str:

    if not isinstance(password, str):
        password = str(password)

    pw_bytes = password.encode("utf-8")
    if len(pw_bytes) > 72:
        password = hashlib.sha256(pw_bytes).hexdigest()

    return password

def hash_password(password: str) -> str:
    normalized_pw = _normalize_password(password)
    return pwd_context.hash(normalized_pw)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    normalized_pw = _normalize_password(plain_password)
    try:
        return pwd_context.verify(normalized_pw, hashed_password)
    except Exception:
        return False

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def decode_token(token: str):
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        email: str = payload.get("sub")
        return email
    except JWTError:
        return None
