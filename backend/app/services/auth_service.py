# @author zhangzhihao
"""用户注册/登录业务。"""

from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import Tenant, User
from app.schemas.auth import AuthUserResponse, RegisterRequest


class AuthService:
    """鉴权 CRUD。"""

    def __init__(self, db: Session) -> None:
        self._db = db

    def register(self, body: RegisterRequest) -> tuple[User, Tenant]:
        existing = self._db.query(User).filter(User.email == body.email.lower()).first()
        if existing:
            raise ValueError("邮箱已注册")

        tenant = Tenant(name=body.tenant_name.strip() or "我的工作区")
        self._db.add(tenant)
        self._db.flush()

        user = User(
            tenant_id=tenant.id,
            email=body.email.lower().strip(),
            password_hash=hash_password(body.password),
            display_name=body.display_name.strip() or body.email.split("@")[0],
        )
        self._db.add(user)
        self._db.commit()
        self._db.refresh(user)
        self._db.refresh(tenant)
        return user, tenant

    def login(self, email: str, password: str) -> User | None:
        user = self._db.query(User).filter(User.email == email.lower().strip()).first()
        if not user or not verify_password(password, user.password_hash):
            return None
        return user

    def get_user(self, user_id: str) -> User | None:
        return self._db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def to_user_response(user: User, tenant: Tenant) -> AuthUserResponse:
        return AuthUserResponse(
            id=user.id,
            email=user.email,
            display_name=user.display_name or user.email,
            tenant_id=tenant.id,
            tenant_name=tenant.name,
        )

    def issue_token(self, user: User) -> str:
        return create_access_token(user.id, user.tenant_id)
