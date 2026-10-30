from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterIn(BaseModel):
    username: str = Field(min_length=3, max_length=50, pattern=r"^[A-Za-z0-9_]+$", description="字母/数字/下划线")
    password: str = Field(min_length=8, max_length=72)
    email: EmailStr
    nickname: str | None = Field(default=None, max_length=50)


class LoginIn(BaseModel):
    username: str = Field(max_length=50)
    password: str = Field(max_length=72)


class RefreshIn(BaseModel):
    refresh_token: str


class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserOut(BaseModel):
    """对外用户信息：绝不含 password_hash / token_version。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: EmailStr
    nickname: str | None
    avatar: str | None
    role_code: str
    status: int
    created_at: datetime
