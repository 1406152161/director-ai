# @author zhangzhihao
"""FastAPI 应用入口。"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import health, novels, projects
from app.core.config import get_settings
from app.core.database import init_db

settings = get_settings()
outputs_path = Path(settings.outputs_dir)
outputs_path.mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(_app: FastAPI):
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
app.include_router(projects.router, prefix="/api")
app.include_router(novels.router, prefix="/api")
app.mount("/outputs", StaticFiles(directory=str(outputs_path)), name="outputs")


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "director-ai API", "docs": "/docs"}
