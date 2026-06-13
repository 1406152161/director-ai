# @author zhangzhihao
"""小说生成编排：规划 → 写前 N 章 → Chroma 记忆。"""

import logging

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.services.novel_memory_service import NovelMemoryService, parse_bible
from app.services.novel_plan_service import NovelPlanService
from app.services.novel_service import NovelService
from app.services.novel_write_service import NovelWriteService

logger = logging.getLogger(__name__)


def _outline_entry(bible: dict, index: int) -> dict | None:
    for item in bible.get("outline") or []:
        if item.get("index") == index:
            return item
    return None


async def _write_single_chapter(
    novel_id: str,
    chapter_index: int,
    novel_svc: NovelService,
    write_svc: NovelWriteService,
    memory_svc: NovelMemoryService,
) -> None:
    novel = novel_svc.get_novel(novel_id)
    if not novel:
        return

    bible = parse_bible(novel.bible_json)
    outline = _outline_entry(bible, chapter_index)
    if not outline:
        raise ValueError(f"大纲中不存在第 {chapter_index} 章")

    title = outline.get("title", f"第{chapter_index}章")
    chapter = novel_svc.get_chapter(novel_id, chapter_index)
    if not chapter:
        chapter = novel_svc.create_chapter_placeholder(novel_id, chapter_index, title)
    novel_svc.update_status(novel_id, novel.status, novel.progress)

    novel_svc.set_chapter_status(chapter.id, "writing")

    prev_tail = ""
    if chapter_index > 1:
        prev = novel_svc.get_chapter(novel_id, chapter_index - 1)
        if prev and prev.content:
            prev_tail = prev.content

    query = f"第{chapter_index}章 {title} {outline.get('summary', '')}"
    snippets = memory_svc.query_relevant(novel_id, query)

    content, summary, word_count = await write_svc.write_chapter(
        novel.premise,
        novel.genre,
        bible,
        outline,
        snippets,
        prev_tail,
    )

    novel_svc.save_chapter(chapter.id, title, content, summary, word_count, "completed")
    memory_svc.add_chapter_summary(novel_id, chapter_index, title, summary)

    fact = f"第{chapter_index}章《{title}》：{summary[:120]}"
    bible = memory_svc.append_fact_to_bible(bible, fact)
    novel_svc.save_bible(novel_id, bible)


async def run_novel_generation(novel_id: str) -> None:
    """后台任务：规划 + 写前 N 章。"""
    db = SessionLocal()
    try:
        novel_svc = NovelService(db)
        plan_svc = NovelPlanService()
        write_svc = NovelWriteService()
        memory_svc = NovelMemoryService()
        settings = get_settings()

        novel = novel_svc.get_novel(novel_id)
        if not novel:
            logger.error("小说不存在: %s", novel_id)
            return

        try:
            novel_svc.update_status(novel_id, "planning", 5)
            plan = await plan_svc.generate_plan(novel.premise, novel.genre)
            novel_svc.apply_plan(novel_id, plan)
            novel_svc.update_status(novel_id, "writing", 20)

            initial = settings.novel_initial_chapters
            for i in range(1, initial + 1):
                await _write_single_chapter(
                    novel_id, i, novel_svc, write_svc, memory_svc
                )
                progress = 20 + int(70 * i / initial)
                novel_svc.update_status(novel_id, "writing", progress)

            novel_svc.update_status(novel_id, "completed", 100)
            logger.info("小说生成完成: %s", novel_id)

        except Exception as exc:
            logger.exception("小说生成失败: %s", novel_id)
            novel_svc.set_failed(novel_id, str(exc))

    finally:
        db.close()


async def run_novel_next_chapter(novel_id: str) -> None:
    """后台任务：续写下一章。"""
    db = SessionLocal()
    try:
        novel_svc = NovelService(db)
        write_svc = NovelWriteService()
        memory_svc = NovelMemoryService()

        novel = novel_svc.get_novel(novel_id)
        if not novel:
            return

        next_index = novel_svc.next_chapter_index(novel_id)
        bible = parse_bible(novel.bible_json)
        if not _outline_entry(bible, next_index):
            novel_svc.set_failed(novel_id, f"大纲已无第 {next_index} 章可写")
            return

        try:
            novel_svc.update_status(novel_id, "writing", novel.progress)
            await _write_single_chapter(
                novel_id, next_index, novel_svc, write_svc, memory_svc
            )
            novel_svc.update_status(novel_id, "completed", 100)
        except Exception as exc:
            logger.exception("续写失败: %s", novel_id)
            novel_svc.set_failed(novel_id, str(exc))

    finally:
        db.close()
