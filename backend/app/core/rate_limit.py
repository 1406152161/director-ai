# @author zhangzhihao
"""限流异常响应。"""

from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded


async def rate_limit_exceeded_handler(_request: Request, _exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(status_code=429, content={"detail": "请求过于频繁，请稍后再试"})
