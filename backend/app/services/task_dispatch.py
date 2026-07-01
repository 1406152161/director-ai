# @author zhangzhihao
"""长任务调度：BackgroundTasks（默认）或 Celery + Redis。"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.config import get_settings

if TYPE_CHECKING:
    from fastapi import BackgroundTasks


def use_celery() -> bool:
    return get_settings().use_celery


def enqueue_video_generation(background_tasks: BackgroundTasks, project_id: str) -> None:
    if use_celery():
        from app.tasks.video_tasks import run_video_generation_task

        run_video_generation_task.delay(project_id)
        return
    from app.services.generation_service import run_generation

    background_tasks.add_task(run_generation, project_id)


def enqueue_novel_generation(background_tasks: BackgroundTasks, novel_id: str) -> None:
    if use_celery():
        from app.tasks.novel_tasks import run_novel_generation_task

        run_novel_generation_task.delay(novel_id)
        return
    from app.services.novel_generation_service import run_novel_generation

    background_tasks.add_task(run_novel_generation, novel_id)


def enqueue_novel_start_writing(
    background_tasks: BackgroundTasks,
    novel_id: str,
    write_count: int,
) -> None:
    if use_celery():
        from app.tasks.novel_tasks import run_novel_start_writing_task

        run_novel_start_writing_task.delay(novel_id, write_count)
        return
    from app.services.novel_generation_service import run_novel_start_writing

    background_tasks.add_task(run_novel_start_writing, novel_id, write_count)


def enqueue_novel_next_chapter(
    background_tasks: BackgroundTasks,
    novel_id: str,
    write_count: int,
) -> None:
    if use_celery():
        from app.tasks.novel_tasks import run_novel_next_chapter_task

        run_novel_next_chapter_task.delay(novel_id, write_count)
        return
    from app.services.novel_generation_service import run_novel_next_chapter

    background_tasks.add_task(run_novel_next_chapter, novel_id, write_count)


def enqueue_approve_chapter(
    background_tasks: BackgroundTasks,
    novel_id: str,
    chapter_index: int,
) -> None:
    if use_celery():
        from app.tasks.novel_tasks import run_approve_chapter_task

        run_approve_chapter_task.delay(novel_id, chapter_index)
        return
    from app.services.novel_generation_service import run_approve_chapter

    background_tasks.add_task(run_approve_chapter, novel_id, chapter_index)


def enqueue_rewrite_chapter(
    background_tasks: BackgroundTasks,
    novel_id: str,
    chapter_index: int,
) -> None:
    if use_celery():
        from app.tasks.novel_tasks import run_rewrite_chapter_task

        run_rewrite_chapter_task.delay(novel_id, chapter_index)
        return
    from app.services.novel_generation_service import run_rewrite_chapter

    background_tasks.add_task(run_rewrite_chapter, novel_id, chapter_index)


def enqueue_replan_novel(background_tasks: BackgroundTasks, novel_id: str) -> None:
    if use_celery():
        from app.tasks.novel_tasks import run_replan_novel_task

        run_replan_novel_task.delay(novel_id)
        return
    from app.services.novel_generation_service import run_replan_novel

    background_tasks.add_task(run_replan_novel, novel_id)
