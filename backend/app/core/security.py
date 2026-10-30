from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"


def hash_password(plain: str) -> str:
    return pwd_ctx.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(plain, hashed)


def create_token(*, user_id: int, token_type: str, token_version: int, expires_minutes: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "type": token_type,
        "tv": token_version,
        "iat": now,
        "exp": now + timedelta(minutes=expires_minutes),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_token_pair(*, user_id: int, token_version: int) -> dict:
    access = create_token(
        user_id=user_id, token_type=TOKEN_TYPE_ACCESS,
        token_version=token_version, expires_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )
    refresh = create_token(
        user_id=user_id, token_type=TOKEN_TYPE_REFRESH,
        token_version=token_version, expires_minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES,
    )
    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


def decode_token(token: str) -> dict:
    """解码失败或过期抛出 JWTError，由调用方转为业务异常。"""
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
