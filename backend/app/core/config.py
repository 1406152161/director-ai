# @author zhangzhihao
"""应用配置，从环境变量 / .env 读取。"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """全局配置项。"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    app_port: int = 8000
    frontend_url: str = "http://localhost:5173"

    # Provider 选择（M0 占位，后续按厂商切换）
    llm_provider: str = "mock"
    image_provider: str = "mock"
    video_provider: str = "mock"
    tts_provider: str = "mock"

    # 数据库与队列（M1+ 启用）
    database_url: str = "sqlite:///./director_ai.db"
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"


@lru_cache
def get_settings() -> Settings:
    return Settings()
