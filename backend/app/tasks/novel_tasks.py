# @author zhangzhihao
"""小说生成 Celery 任务。"""

from app.services.novel_generation_service import (
    run_approve_chapter,
    run_novel_generation,
    run_novel_next_chapter,
    run_novel_start_writing,
    run_replan_novel,
    run_rewrite_chapter,
)
from app.tasks.async_runner import run_async
from app.tasks.celery_app import celery_app


@celery_app.task(name="director.run_novel_generation", bind=True, max_retries=0)
def run_novel_generation_task(self, novel_id: str) -> dict[str, str]:
    run_async(run_novel_generation, novel_id)
    return {"novel_id": novel_id, "status": "finished"}


@celery_app.task(name="director.run_novel_start_writing", bind=True, max_retries=0)
def run_novel_start_writing_task(self, novel_id: str, write_count: int) -> dict[str, str]:
    run_async(run_novel_start_writing, novel_id, write_count)
    return {"novel_id": novel_id, "status": "finished"}


@celery_app.task(name="director.run_novel_next_chapter", bind=True, max_retries=0)
def run_novel_next_chapter_task(self, novel_id: str, write_count: int) -> dict[str, str]:
    run_async(run_novel_next_chapter, novel_id, write_count)
    return {"novel_id": novel_id, "status": "finished"}


@celery_app.task(name="director.run_approve_chapter", bind=True, max_retries=0)
def run_approve_chapter_task(self, novel_id: str, chapter_index: int) -> dict[str, str]:
    run_async(run_approve_chapter, novel_id, chapter_index)
    return {"novel_id": novel_id, "status": "finished"}


@celery_app.task(name="director.run_rewrite_chapter", bind=True, max_retries=0)
def run_rewrite_chapter_task(self, novel_id: str, chapter_index: int) -> dict[str, str]:
    run_async(run_rewrite_chapter, novel_id, chapter_index)
    return {"novel_id": novel_id, "status": "finished"}


@celery_app.task(name="director.run_replan_novel", bind=True, max_retries=0)
def run_replan_novel_task(self, novel_id: str) -> dict[str, str]:
    run_async(run_replan_novel, novel_id)
    return {"novel_id": novel_id, "status": "finished"}
