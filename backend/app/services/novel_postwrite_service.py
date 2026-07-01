# @author zhangzhihao
"""写后管线：抽取 + 滚动摘要 + 条件 replan。"""

import json
import logging

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.services.novel_entity_service import NovelEntityService
from app.services.novel_extract_service import NovelExtractService
from app.services.novel_framework_service import NovelFrameworkService
from app.services.novel_memory_service import NovelMemoryService, parse_bible
from app.services.novel_replan_service import NovelReplanService
from app.services.novel_service import NovelService
from app.services.novel_summary_service import NovelSummaryService

logger = logging.getLogger(__name__)


def get_plant_snippets(
    novel_svc: NovelService,
    novel_id: str,
    foreshadowing: list[dict],
    chapter_index: int,
) -> list[dict]:
    """回收伏笔时注入埋设章原文片段。"""
    snippets: list[dict] = []
    for fs in foreshadowing:
        if fs.get("resolve_chapter") != chapter_index:
            continue
        plant_ch = fs.get("plant_chapter")
        if not plant_ch:
            continue
        ch = novel_svc.get_chapter(novel_id, plant_ch)
        excerpt = ""
        if ch and ch.content:
            excerpt = ch.content[:800]
        elif ch and ch.summary:
            excerpt = ch.summary
        snippets.append({
            "id": fs.get("id"),
            "plant_chapter": plant_ch,
            "excerpt": excerpt or "（埋设章暂无正文）",
        })
    return snippets


class NovelPostwriteService:
    """章节校验通过后的记忆与摘要更新。"""

    def __init__(self, db: Session) -> None:
        self._db = db
        self._novel_svc = NovelService(db)
        self._entity_svc = NovelEntityService(db)
        self._framework_svc = NovelFrameworkService(db)
        self._memory_svc = NovelMemoryService()
        self._extract_svc = NovelExtractService()
        self._summary_svc = NovelSummaryService()
        self._replan_svc = NovelReplanService()
        self._settings = get_settings()

    async def finalize_chapter(
        self,
        novel_id: str,
        chapter_index: int,
        title: str,
        content: str,
        summary: str,
    ) -> None:
        novel = self._novel_svc.get_novel(novel_id)
        if not novel:
            return

        merged_bible, entity_updates, _, _ = await self._extract_svc.extract_after_chapter(
            chapter_index, title, content, summary, novel.bible_json
        )
        self._entity_svc.apply_extraction(novel_id, chapter_index, entity_updates)

        bible_json = json.dumps(merged_bible, ensure_ascii=False)
        bible_json = await self._summary_svc.update_rolling_summary(
            bible_json, chapter_index, summary
        )
        bible = parse_bible(bible_json)

        self._memory_svc.add_chapter_summary(novel_id, chapter_index, title, summary)
        self._novel_svc.sync_bible_indexes(novel_id, bible)

        interval = self._settings.novel_replan_interval
        if interval > 0 and chapter_index % interval == 0:
            await self._maybe_replan(novel_id, chapter_index)

    async def _maybe_replan(self, novel_id: str, last_written: int) -> None:
        from app.services.novel_outline_service import NovelOutlineService

        novel = self._novel_svc.get_novel(novel_id)
        if not novel:
            return
        summaries = [
            ch.summary
            for ch in sorted(novel.chapters or [], key=lambda c: c.index)
            if ch.status == "completed" and ch.summary
        ]
        merged_outline, foreshadowing = await self._replan_svc.replan_unwritten(
            novel_id,
            self._db,
            novel.premise,
            novel.genre,
            novel.bible_json,
            last_written,
            summaries,
        )
        bible = parse_bible(novel.bible_json)
        bible["foreshadowing"] = foreshadowing

        outline_svc = NovelOutlineService(self._db)
        use_db = bool(bible.get("meta", {}).get("outline_in_db")) or outline_svc.count_by_level(novel_id) > 0
        unwritten = [o for o in merged_outline if int(o.get("index", 0)) > last_written]
        if use_db and unwritten:
            outline_svc.upsert_batch(novel_id, unwritten, detail_level="detailed")
        elif not use_db:
            bible["outline"] = merged_outline

        self._novel_svc.sync_bible_indexes(novel_id, bible)
        logger.info("Replan 完成 novel=%s after chapter=%s", novel_id, last_written)
