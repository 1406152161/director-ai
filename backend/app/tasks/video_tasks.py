# @author zhangzhihao
"""视频生成 Celery 任务。"""

from app.services.generation_service import run_generation
from app.tasks.async_runner import run_async
from app.tasks.celery_app import celery_app


@celery_app.task(name="director.run_video_generation", bind=True, max_retries=0)
def run_video_generation_task(self, project_id: str) -> dict[str, str]:
    run_async(run_generation, project_id)
    return {"project_id": project_id, "status": "finished"}
