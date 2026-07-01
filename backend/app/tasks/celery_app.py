# @author zhangzhihao
"""Celery 应用初始化。"""

from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "director_ai",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.tasks.video_tasks",
        "app.tasks.novel_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)
