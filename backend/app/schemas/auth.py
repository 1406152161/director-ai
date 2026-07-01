# @author zhangzhihao
"""鉴权相关 Schema。"""

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    email: str = Field(min_length=3, max_length=256)
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(default="", max_length=128)
    tenant_name: str = Field(default="我的工作区", max_length=128)


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthUserResponse(BaseModel):
    id: str
    email: str
    display_name: str
    tenant_id: str
    tenant_name: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: AuthUserResponse
