from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import error_codes as ec
from app.core.error_codes import biz_error
from app.core.security import (
    TOKEN_TYPE_ACCESS,
    TOKEN_TYPE_REFRESH,
    create_token_pair,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import SysRole, SysUser
from app.schemas.user import RegisterIn, UserOut

DEFAULT_USER_ROLE_ID = 2


def _to_user_out(user: SysUser) -> UserOut:
    return UserOut(
        id=user.id,
        username=user.username,
        email=user.email,
        nickname=user.nickname,
        avatar=user.avatar,
        role_code=user.role.code,
        status=user.status,
        created_at=user.created_at,
    )


def register(db: Session, data: RegisterIn) -> UserOut:
    exists = db.scalar(
        select(SysUser.id).where(
            SysUser.is_deleted == 0,
            (SysUser.username == data.username) | (SysUser.email == data.email),
        )
    )
    if exists:
        raise biz_error(ec.E_USERNAME_OR_EMAIL_TAKEN)

    user = SysUser(
        username=data.username,
        password_hash=hash_password(data.password),
        email=data.email,
        nickname=data.nickname or data.username,
        role_id=DEFAULT_USER_ROLE_ID,
        status=1,
        token_version=0,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _to_user_out(user)


def _authenticate(db: Session, username: str, password: str) -> SysUser:
    user = db.scalar(
        select(SysUser).where(SysUser.username == username, SysUser.is_deleted == 0)
    )
    if user is None or not verify_password(password, user.password_hash):
        raise biz_error(ec.E_BAD_CREDENTIALS)
    if user.status != 1:
        raise biz_error(ec.E_ACCOUNT_DISABLED)
    return user


def login(db: Session, username: str, password: str) -> dict:
    user = _authenticate(db, username, password)
    user.last_login_at = datetime.utcnow()
    db.commit()
    tokens = create_token_pair(user_id=user.id, token_version=user.token_version)
    return {"tokens": tokens, "user": _to_user_out(user)}


def refresh(db: Session, refresh_token: str) -> dict:
    try:
        payload = decode_token(refresh_token)
    except Exception as exc:  # noqa: BLE001 - jose 抛 JWTError/ExpiredSignatureError
        raise biz_error(ec.E_TOKEN_INVALID) from exc
    if payload.get("type") != TOKEN_TYPE_REFRESH:
        raise biz_error(ec.E_TOKEN_TYPE_MISMATCH)

    user = db.get(SysUser, int(payload["sub"]))
    if user is None or user.is_deleted != 0 or user.status != 1:
        raise biz_error(ec.E_TOKEN_INVALID)
    if user.token_version != payload.get("tv"):
        # 版本不匹配：该 refresh token 已因登出/再次刷新被作废
        raise biz_error(ec.E_TOKEN_INVALID)

    # 旋转：版本号+1，旧的 access/refresh 全部失效
    user.token_version += 1
    db.commit()
    tokens = create_token_pair(user_id=user.id, token_version=user.token_version)
    return {"tokens": tokens, "user": _to_user_out(user)}


def logout(db: Session, user: SysUser) -> None:
    # 版本号+1 使其名下所有 access/refresh token 立即失效
    user.token_version += 1
    db.commit()


def authenticate_access_token(db: Session, token: str) -> SysUser:
    try:
        payload = decode_token(token)
    except Exception as exc:  # noqa: BLE001
        raise biz_error(ec.E_TOKEN_INVALID) from exc
    if payload.get("type") != TOKEN_TYPE_ACCESS:
        raise biz_error(ec.E_TOKEN_TYPE_MISMATCH)

    user = db.get(SysUser, int(payload["sub"]))
    if user is None or user.is_deleted != 0:
        raise biz_error(ec.E_TOKEN_INVALID)
    if user.status != 1:
        raise biz_error(ec.E_ACCOUNT_DISABLED)
    if user.token_version != payload.get("tv"):
        raise biz_error(ec.E_TOKEN_INVALID)
    return user
