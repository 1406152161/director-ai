# @author zhangzhihao
"""鉴权 API。"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.api.deps import get_auth_context
from app.core.config import get_settings
from app.core.database import get_db
from app.core.limiter import limiter
from app.models.user import Tenant
from app.schemas.auth import AuthUserResponse, LoginRequest, RegisterRequest, TokenResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
@limiter.limit("5/minute")  # 防刷注册
async def register(
    request: Request,
    body: RegisterRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    if not get_settings().auth_enabled:
        raise HTTPException(status_code=503, detail="鉴权未启用")
    svc = AuthService(db)
    try:
        user, tenant = svc.register(body)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return TokenResponse(
        access_token=svc.issue_token(user),
        user=svc.to_user_response(user, tenant),
    )


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(
    request: Request,
    body: LoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    if not get_settings().auth_enabled:
        raise HTTPException(status_code=503, detail="鉴权未启用")
    svc = AuthService(db)
    user = svc.login(body.email, body.password)
    if not user:
        raise HTTPException(status_code=401, detail="邮箱或密码错误")
    tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=500, detail="租户数据异常")
    return TokenResponse(
        access_token=svc.issue_token(user),
        user=svc.to_user_response(user, tenant),
    )


@router.get("/me", response_model=AuthUserResponse)
async def me(
    db: Session = Depends(get_db),
    ctx=Depends(get_auth_context),
) -> AuthUserResponse:
    if not get_settings().auth_enabled:
        raise HTTPException(status_code=503, detail="鉴权未启用")
    if ctx is None:
        raise HTTPException(status_code=401, detail="未登录")
    user = AuthService(db).get_user(ctx.user_id)
    tenant = db.query(Tenant).filter(Tenant.id == ctx.tenant_id).first()
    if not user or not tenant:
        raise HTTPException(status_code=401, detail="用户不存在")
    return AuthService.to_user_response(user, tenant)


@router.get("/status")
async def auth_status() -> dict[str, bool]:
    return {"enabled": get_settings().auth_enabled}
