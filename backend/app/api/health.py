# @author zhangzhihao
"""健康检查路由。"""

import logging

from fastapi import APIRouter, Query
from sqlalchemy import text

logger = logging.getLogger(__name__)

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
        # 对外不暴露异常详情，仅记录日志
        logger.warning("Health check database error: %s", exc)
        checks["database"] = "unavailable"
        body["status"] = "degraded"

    try:
        import redis

        from app.core.config import get_settings

        client = redis.from_url(get_settings().redis_url, socket_connect_timeout=0.5)
        client.ping()
        checks["redis"] = "ok"
    except Exception as exc:
        logger.warning("Health check redis error: %s", exc)
        checks["redis"] = "unavailable"
        body["status"] = "degraded"

    body["checks"] = checks
    return body
