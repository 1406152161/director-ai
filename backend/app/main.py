# @author zhangzhihao
"""FastAPI 应用入口。"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import articles, auth, health, novels, projects
from app.core.config import get_settings
from app.core.database import init_db

logger = logging.getLogger(__name__)
settings = get_settings()
outputs_path = Path(settings.outputs_dir)
outputs_path.mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # 启动日志提醒运维确认鉴权开关
    if settings.auth_enabled:
        logger.info("认证已启用")
    else:
        logger.warning("认证已关闭，所有 API 无需鉴权")
    init_db()
    yield

app = FastAPI(
    title="director-ai",
    description="AI 自动视频导演平台 API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(projects.router, prefix="/api")
app.include_router(novels.router, prefix="/api")
app.include_router(articles.router, prefix="/api")
app.mount("/outputs", StaticFiles(directory=str(outputs_path)), name="outputs")


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "director-ai API", "docs": "/docs"}
