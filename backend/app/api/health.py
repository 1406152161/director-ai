# @author zhangzhihao
"""健康检查路由。"""

from fastapi import APIRouter, Query
from sqlalchemy import text

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check(deep: bool = Query(False)) -> dict:
    body: dict = {"status": "ok", "service": "director-ai"}
    if not deep:
        return body

    checks: dict[str, str] = {}

    try:
        from app.core.database import engine

        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:
        checks["database"] = f"error: {exc}"
        body["status"] = "degraded"

    try:
        import redis

        from app.core.config import get_settings

        client = redis.from_url(get_settings().redis_url, socket_connect_timeout=0.5)
        client.ping()
        checks["redis"] = "ok"
    except Exception as exc:
        checks["redis"] = f"error: {exc}"
        body["status"] = "degraded"

    body["checks"] = checks
    return body
