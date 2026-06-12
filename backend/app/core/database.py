# @author zhangzhihao
"""数据库引擎与会话管理。"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

_settings = get_settings()

_connect_args = (
    {"check_same_thread": False} if _settings.database_url.startswith("sqlite") else {}
)

engine = create_engine(_settings.database_url, connect_args=_connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI 依赖：请求级数据库会话。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """启动时建表并执行幂等迁移。"""
    from app.core.migrate import run_migrations  # noqa: PLC0415
    from app.models import Base  # noqa: PLC0415 — 延迟导入避免循环依赖

    Base.metadata.create_all(bind=engine)
    run_migrations(engine)
