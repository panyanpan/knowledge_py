from typing import Callable

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core import error_codes as ec
from app.core.database import get_db
from app.core.error_codes import biz_error
from app.models.user import SysUser
from app.services.auth_service import authenticate_access_token

# tokenUrl 指向 OAuth2 表单登录端点，供 Swagger Authorize 按钮使用
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login/form", auto_error=False)


def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> SysUser:
    if not token:
        raise biz_error(ec.E_TOKEN_INVALID)
    return authenticate_access_token(db, token)


def get_current_user_optional(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> SysUser | None:
    """匿名接口用：未登录或 token 无效返回 None，不报错。"""
    if not token:
        return None
    try:
        return authenticate_access_token(db, token)
    except Exception:  # noqa: BLE001 - 匿名场景下无效 token 视为未登录
        return None


def require_role(*role_codes: str) -> Callable[[SysUser], SysUser]:
    """RBAC 依赖：require_role("ADMIN")。"""

    def checker(user: SysUser = Depends(get_current_user)) -> SysUser:
        if user.role.code not in role_codes:
            raise biz_error(ec.E_FORBIDDEN)
        return user

    return checker
