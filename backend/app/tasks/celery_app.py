# @author zhangzhihao
"""Celery 应用初始化。"""

from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "director_ai",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
)


@celery_app.task(name="pipeline.run_video_pipeline")
def run_video_pipeline(project_id: str) -> dict[str, str]:
    """异步执行视频生成 Pipeline（M1 接入 LangGraph）。"""
    # TODO: 调用 app.pipeline.graph 执行工作流
    return {"project_id": project_id, "status": "queued"}
