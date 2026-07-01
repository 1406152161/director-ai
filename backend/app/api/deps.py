# @author zhangzhihao
"""FastAPI 鉴权依赖。"""

from dataclasses import dataclass

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import decode_access_token
from app.services.auth_service import AuthService

_bearer = HTTPBearer(auto_error=False)


@dataclass
class AuthContext:
    user_id: str
    tenant_id: str


def get_auth_context(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> AuthContext | None:
    settings = get_settings()
    if not settings.auth_enabled:
        return None
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="未登录")
    try:
        payload = decode_access_token(credentials.credentials)
    except Exception as exc:
        raise HTTPException(status_code=401, detail="登录已失效") from exc
    user = AuthService(db).get_user(payload["user_id"])
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    return AuthContext(user_id=user.id, tenant_id=user.tenant_id)


def require_auth(ctx: AuthContext | None = Depends(get_auth_context)) -> AuthContext:
    if ctx is None:
        settings = get_settings()
        if settings.auth_enabled:
            raise HTTPException(status_code=401, detail="未登录")
        raise HTTPException(status_code=500, detail="鉴权未启用")
    return ctx


def optional_owner_id(ctx: AuthContext | None = Depends(get_auth_context)) -> str | None:
    return ctx.user_id if ctx else None
