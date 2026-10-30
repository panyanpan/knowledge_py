from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.response import ok
from app.models.user import SysUser
from app.schemas.user import LoginIn, RefreshIn, RegisterIn
from app.services import auth_service
from app.services.auth_service import _to_user_out

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register")
def register(data: RegisterIn, db: Session = Depends(get_db)):
    user = auth_service.register(db, data)
    return ok(user.model_dump(), message="注册成功")


@router.post("/login")
def login(data: LoginIn, db: Session = Depends(get_db)):
    result = auth_service.login(db, data.username, data.password)
    return ok(result, message="登录成功")


@router.post("/login/form", summary="OAuth2 表单登录（供 Swagger Authorize 使用）")
def login_form(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    result = auth_service.login(db, form.username, form.password)
    return ok(result, message="登录成功")


@router.post("/refresh")
def refresh(data: RefreshIn, db: Session = Depends(get_db)):
    result = auth_service.refresh(db, data.refresh_token)
    return ok(result, message="刷新成功")


@router.post("/logout")
def logout(
    user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    auth_service.logout(db, user)
    return ok(None, message="已登出")


@router.get("/me")
def me(user: SysUser = Depends(get_current_user)):
    return ok(_to_user_out(user).model_dump())
