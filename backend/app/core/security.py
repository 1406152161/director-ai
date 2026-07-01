# @author zhangzhihao
"""密码哈希与 JWT 工具。"""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

import jwt

from app.core.config import get_settings

_PBKDF2_ITERATIONS = 120_000


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        _PBKDF2_ITERATIONS,
    )
    return f"{salt}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt, hex_digest = stored.split("$", 1)
    except ValueError:
        return False
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        _PBKDF2_ITERATIONS,
    )
    return secrets.compare_digest(digest.hex(), hex_digest)


def create_access_token(user_id: str, tenant_id: str) -> str:
    settings = get_settings()
    expire = datetime.now(UTC) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {
        "sub": user_id,
        "tenant_id": tenant_id,
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_access_token(token: str) -> dict[str, str]:
    settings = get_settings()
    data = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    return {
        "user_id": str(data["sub"]),
        "tenant_id": str(data["tenant_id"]),
    }
