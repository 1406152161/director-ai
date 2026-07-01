# @author zhangzhihao
"""小说 CRUD、导出与 Story Bible 持久化。"""

import json

from sqlalchemy.orm import Session, joinedload

from app.models.novel import Novel, NovelChapter
from app.novel.prompts import VALID_GENRES, genre_label
from app.schemas.novel import NovelCreate, NovelListItem, NovelResponse, NovelChapterResponse
from app.services.novel_memory_service import parse_bible
from app.services.progress_hub import emit_progress


class NovelService:
    """小说业务服务。"""

    def __init__(self, db: Session) -> None:
        self._db = db

    def create_novel(self, body: NovelCreate, owner_id: str | None = None) -> Novel:
        if body.genre not in VALID_GENRES:
            raise ValueError(f"不支持的题材: {body.genre}")
        bible = parse_bible("{}")
        bible["meta"] = {
            "target_chapters_user": body.target_chapters,
        }
        novel = Novel(
            premise=body.premise,
            genre=body.genre,
            status="pending",
            progress=0,
            bible_json=json.dumps(bible, ensure_ascii=False),
            owner_id=owner_id,
        )
        self._db.add(novel)
        self._db.commit()
        self._db.refresh(novel)
        return novel

    def get_novel(self, novel_id: str) -> Novel | None:
        return (
            self._db.query(Novel)
            .options(joinedload(Novel.chapters))
            .filter(Novel.id == novel_id)
            .first()
        )

    def list_novels(self, owner_id: str | None = None) -> list[Novel]:
        q = self._db.query(Novel).order_by(Novel.created_at.desc())
        if owner_id:
            q = q.filter(Novel.owner_id == owner_id)
        return q.all()

    def _emit_progress(self, novel_id: str) -> None:
        novel = self._db.query(Novel).filter(Novel.id == novel_id).first()
        if not novel:
            return
        emit_progress(
            "novel",
            novel_id,
            status=novel.status,
            progress=novel.progress,
            error=novel.error,
        )

    def update_status(self, novel_id: str, status: str, progress: int | None = None) -> None:
        novel = self._db.query(Novel).filter(Novel.id == novel_id).first()
        if not novel:
            return
        novel.status = status
        if progress is not None:
            novel.progress = progress
        self._db.commit()
        self._emit_progress(novel_id)

    def set_failed(self, novel_id: str, error: str) -> None:
        novel = self._db.query(Novel).filter(Novel.id == novel_id).first()
        if not novel:
            return
        novel.status = "failed"
        novel.error = error
        self._db.commit()
        self._emit_progress(novel_id)

    def reset_for_planning(self, novel_id: str) -> None:
        """清除错误，保留 planning_state 与 outline（手动 retry 续跑）。"""
        novel = self._db.query(Novel).filter(Novel.id == novel_id).first()
        if not novel:
            return
        novel.status = "planning"
        novel.error = None
        bible = parse_bible(novel.bible_json)
        state = (bible.get("meta") or {}).get("planning_state") or {}
        if state:
            state = {**state, "last_error": None}
            bible.setdefault("meta", {})["planning_state"] = state
            novel.bible_json = json.dumps(bible, ensure_ascii=False)
        self._db.commit()
        self._emit_progress(novel_id)

    def set_planning_failed(self, novel_id: str, error: str) -> None:
        novel = self._db.query(Novel).filter(Novel.id == novel_id).first()
        if not novel:
            return
        bible = parse_bible(novel.bible_json)
        meta = bible.setdefault("meta", {})
        state = dict(meta.get("planning_state") or {})
        state["last_error"] = error[:500]
        meta["planning_state"] = state
        novel.bible_json = json.dumps(bible, ensure_ascii=False)
        novel.status = "failed"
        novel.error = error[:500]
        self._db.commit()
        self._emit_progress(novel_id)

    def update_planning_state(
        self,
        novel_id: str,
        *,
        phase: str | None = None,
        l1_done_through: int | None = None,
        l2_done_through: int | None = None,
        progress: int | None = None,
    ) -> None:
        novel = self._db.query(Novel).filter(Novel.id == novel_id).first()
        if not novel:
            return
        bible = parse_bible(novel.bible_json)
        meta = bible.setdefault("meta", {})
        state = dict(meta.get("planning_state") or {})
        if phase is not None:
            state["phase"] = phase
        if l1_done_through is not None:
            state["l1_done_through"] = l1_done_through
        if l2_done_through is not None:
            state["l2_done_through"] = l2_done_through
        state["last_error"] = None
        meta["planning_state"] = state
        novel.bible_json = json.dumps(bible, ensure_ascii=False)
        if progress is not None:
            novel.progress = progress
        novel.status = "planning"
        self._db.commit()
        self._emit_progress(novel_id)

    def apply_l0_plan(self, novel_id: str, world_plan: dict, target_chapters: int | None) -> None:
        """L0 落库：世界观 + 卷弧，不含章纲。"""
        novel = self._db.query(Novel).filter(Novel.id == novel_id).first()
        if not novel:
            return
        existing = parse_bible(novel.bible_json)
        meta = existing.get("meta") or {}
        plan_meta = world_plan.get("meta") or {}
        for key in (
            "total_chapters",
            "target_chapters_user",
            "chapter_flex_range",
            "chapter_count_reason",
        ):
            if plan_meta.get(key) is not None:
                meta[key] = plan_meta[key]
        if target_chapters is not None and "target_chapters_user" not in meta:
            meta["target_chapters_user"] = target_chapters
        meta["total_chapters"] = plan_meta.get("total_chapters") or meta.get("total_chapters")
        meta["planning_state"] = {
            "phase": "l1_skeleton",
            "l1_done_through": 0,
            "l2_done_through": 0,
            "last_error": None,
        }
        meta["outline_in_db"] = True
        bible = {
            "meta": meta,
            "world": world_plan.get("world", ""),
            "power_system": world_plan.get("power_system", ""),
            "items": world_plan.get("items") or [],
            "facts": existing.get("facts") or [],
            "characters": [
                {
                    "name": c.get("name", ""),
                    "role": c.get("role", ""),
                    "traits": c.get("profile") or c.get("traits", ""),
                    "growth_arc": c.get("growth_arc", ""),
                }
                for c in world_plan.get("characters", [])
            ],
            "volumes": world_plan.get("volumes") or [],
            "foreshadowing": world_plan.get("foreshadowing") or [],
            "outline": [],
            "beats": existing.get("beats") or {},
        }
        novel.title = world_plan.get("title", "") or novel.title
        novel.synopsis = world_plan.get("synopsis", "") or novel.synopsis
        novel.bible_json = json.dumps(bible, ensure_ascii=False)
        self._db.commit()

        from app.services.novel_entity_service import NovelEntityService
        from app.services.novel_framework_service import NovelFrameworkService
        from app.services.novel_memory_service import NovelMemoryService

        memory_svc = NovelMemoryService()
        NovelEntityService(self._db).seed_from_bible(novel_id, bible)
        NovelFrameworkService(self._db, memory_svc).sync_from_bible(novel_id, bible)

    def finalize_planned(self, novel_id: str, l2_detail_to: int) -> None:
        """规划完成：同步 outline 向量索引，标记 planned。"""
        novel = self._db.query(Novel).filter(Novel.id == novel_id).first()
        if not novel:
            return
        bible = parse_bible(novel.bible_json)
        meta = bible.setdefault("meta", {})
        meta["l2_detail_to"] = l2_detail_to
        meta["outline_in_db"] = True
        meta["planning_state"] = {
            "phase": "done",
            "l1_done_through": int(meta.get("total_chapters") or 0),
            "l2_done_through": l2_detail_to,
            "last_error": None,
        }
        novel.bible_json = json.dumps(bible, ensure_ascii=False)
        novel.status = "planned"
        novel.progress = 100
        novel.error = None
        self._db.commit()
        self._emit_progress(novel_id)

        from app.services.novel_entity_service import NovelEntityService
        from app.services.novel_framework_service import NovelFrameworkService
        from app.services.novel_memory_service import NovelMemoryService
        from app.services.novel_outline_service import NovelOutlineService

        outline_svc = NovelOutlineService(self._db)
        total = int(meta.get("total_chapters") or 0)
        bible_for_sync = dict(bible)
        bible_for_sync["outline"] = outline_svc.to_bible_outline(
            novel_id, 1, min(total, 500)
        )
        memory_svc = NovelMemoryService()
        NovelEntityService(self._db).seed_from_bible(novel_id, bible_for_sync)
        NovelFrameworkService(self._db, memory_svc).sync_from_bible(novel_id, bible_for_sync)

    def world_plan_from_bible(self, novel: Novel) -> dict:
        bible = parse_bible(novel.bible_json)
        return {
            **bible,
            "title": novel.title,
            "synopsis": novel.synopsis,
            "meta": bible.get("meta") or {},
        }

    def apply_plan(self, novel_id: str, plan: dict) -> None:
        """落库规划结果并初始化 Story Bible。"""
        novel = self._db.query(Novel).filter(Novel.id == novel_id).first()
        if not novel:
            return

        existing = parse_bible(novel.bible_json)
        meta = existing.get("meta") or {}
        plan_meta = plan.get("meta") or {}
        for key in (
            "total_chapters",
            "l2_detail_to",
            "outline_in_db",
            "target_chapters_user",
            "chapter_flex_range",
            "chapter_count_reason",
        ):
            if plan_meta.get(key) is not None:
                meta[key] = plan_meta[key]
        meta["total_chapters"] = meta.get("total_chapters") or len(plan.get("outline") or [])
        meta["outline_in_db"] = True

        outline_items = plan.get("outline") or []
        bible = {
            "meta": meta,
            "world": plan.get("world", ""),
            "power_system": plan.get("power_system", ""),
            "items": plan.get("items") or [],
            "facts": existing.get("facts") or [],
            "characters": [
                {
                    "name": c.get("name", ""),
                    "role": c.get("role", ""),
                    "traits": c.get("profile") or c.get("traits", ""),
                    "growth_arc": c.get("growth_arc", ""),
                }
                for c in plan.get("characters", [])
            ],
            "volumes": plan.get("volumes") or [],
            "foreshadowing": plan.get("foreshadowing") or [],
            "outline": [],
            "beats": existing.get("beats") or {},
        }
        novel.title = plan.get("title", "") or novel.title
        novel.synopsis = plan.get("synopsis", "") or novel.synopsis
        novel.bible_json = json.dumps(bible, ensure_ascii=False)
        self._db.commit()

        from app.services.novel_entity_service import NovelEntityService
        from app.services.novel_framework_service import NovelFrameworkService
        from app.services.novel_memory_service import NovelMemoryService
        from app.services.novel_outline_service import NovelOutlineService

        outline_svc = NovelOutlineService(self._db)
        outline_svc.delete_all(novel_id)
        skeleton_batch = []
        detail_batch = []
        for item in outline_items:
            if item.get("detail_level") == "detailed" or item.get("hook"):
                detail_batch.append(item)
            else:
                skeleton_batch.append(item)
        if skeleton_batch:
            outline_svc.upsert_batch(novel_id, skeleton_batch, detail_level="skeleton", locked=True)
        if detail_batch:
            outline_svc.upsert_batch(novel_id, detail_batch, detail_level="detailed", locked=True)

        memory_svc = NovelMemoryService()
        bible_for_sync = dict(bible)
        bible_for_sync["outline"] = outline_svc.to_bible_outline(
            novel_id, 1, min(int(meta["total_chapters"]), 500)
        )
        NovelEntityService(self._db).seed_from_bible(novel_id, bible_for_sync)
        NovelFrameworkService(self._db, memory_svc).sync_from_bible(novel_id, bible_for_sync)

    def save_bible(self, novel_id: str, bible: dict) -> None:
        novel = self._db.query(Novel).filter(Novel.id == novel_id).first()
        if not novel:
            return
        novel.bible_json = json.dumps(bible, ensure_ascii=False)
        self._db.commit()

    def sync_bible_indexes(self, novel_id: str, bible: dict) -> dict | None:
        """持久化 bible，并将 inline outline 写入 DB 后重 sync entity/framework。"""
        from app.services.novel_entity_service import NovelEntityService
        from app.services.novel_framework_service import NovelFrameworkService
        from app.services.novel_memory_service import NovelMemoryService
        from app.services.novel_outline_service import NovelOutlineService

        bible = dict(bible)
        meta = bible.setdefault("meta", {})
        outline_svc = NovelOutlineService(self._db)
        total = int(meta.get("total_chapters") or 500)

        inline_outline = bible.get("outline") or []
        if inline_outline:
            outline_svc.upsert_batch(novel_id, inline_outline, detail_level="detailed")
            meta["outline_in_db"] = True

        if meta.get("outline_in_db") or outline_svc.count_by_level(novel_id) > 0:
            meta["outline_in_db"] = True
            bible["outline"] = []

        self.save_bible(novel_id, bible)

        memory_svc = NovelMemoryService()
        bible_for_sync = dict(bible)
        bible_for_sync["outline"] = outline_svc.to_bible_outline(
            novel_id, 1, min(total, 500)
        )
        NovelEntityService(self._db).seed_from_bible(novel_id, bible_for_sync)
        NovelFrameworkService(self._db, memory_svc).sync_from_bible(novel_id, bible_for_sync)
        return self._bible_for_response(novel_id, bible)

    def patch_bible(self, novel_id: str, patch: dict) -> dict | None:
        """合并分区更新并 re-sync 向量索引。"""
        novel = self.get_novel(novel_id)
        if not novel:
            return None
        if novel.status == "writing":
            raise ValueError("写作中不可修改规划")

        bible = parse_bible(novel.bible_json)
        for key in ("world", "power_system", "characters", "items", "volumes", "foreshadowing"):
            if key in patch and patch[key] is not None:
                bible[key] = patch[key]
        if patch.get("outline") is not None:
            bible["outline"] = patch["outline"]
        return self.sync_bible_indexes(novel_id, bible)

    def clear_review_block_if_none(self, novel_id: str) -> None:
        if self.has_blocking_review(novel_id):
            return
        novel = self._db.query(Novel).filter(Novel.id == novel_id).first()
        if novel and novel.status == "review_required":
            novel.status = "completed"
            self._db.commit()

    def get_chapter(self, novel_id: str, index: int) -> NovelChapter | None:
        return (
            self._db.query(NovelChapter)
            .filter(NovelChapter.novel_id == novel_id, NovelChapter.index == index)
            .first()
        )

    def create_chapter_placeholder(self, novel_id: str, index: int, title: str) -> NovelChapter:
        chapter = NovelChapter(
            novel_id=novel_id,
            index=index,
            title=title,
            status="pending",
        )
        self._db.add(chapter)
        self._db.commit()
        self._db.refresh(chapter)
        return chapter

    def save_chapter(
        self,
        chapter_id: str,
        title: str,
        content: str,
        summary: str,
        word_count: int,
        status: str = "completed",
        validation_status: str = "passed",
        validation_score: int = 0,
        validation_issues: str = "[]",
    ) -> None:
        chapter = self._db.query(NovelChapter).filter(NovelChapter.id == chapter_id).first()
        if not chapter:
            return
        chapter.title = title
        chapter.content = content
        chapter.summary = summary
        chapter.word_count = word_count
        chapter.status = status
        chapter.validation_status = validation_status
        chapter.validation_score = validation_score
        chapter.validation_issues = validation_issues
        self._db.commit()

    def has_blocking_review(self, novel_id: str) -> bool:
        """是否存在待复核章节（拦截续写）。"""
        row = (
            self._db.query(NovelChapter)
            .filter(
                NovelChapter.novel_id == novel_id,
                NovelChapter.status == "needs_review",
            )
            .first()
        )
        return row is not None

    def set_review_required(self, novel_id: str, progress: int | None = None) -> None:
        self.update_status(novel_id, "review_required", progress)

    def set_chapter_status(self, chapter_id: str, status: str) -> None:
        chapter = self._db.query(NovelChapter).filter(NovelChapter.id == chapter_id).first()
        if not chapter:
            return
        chapter.status = status
        self._db.commit()

    def set_chapter_failed(self, chapter_id: str, error: str) -> None:
        chapter = self._db.query(NovelChapter).filter(NovelChapter.id == chapter_id).first()
        if not chapter:
            return
        chapter.status = "failed"
        chapter.content = error
        self._db.commit()

    def next_chapter_index(self, novel_id: str) -> int:
        last = (
            self._db.query(NovelChapter)
            .filter(NovelChapter.novel_id == novel_id)
            .order_by(NovelChapter.index.desc())
            .first()
        )
        return (last.index + 1) if last else 1

    def export_novel(self, novel_id: str, fmt: str) -> tuple[str, str]:
        """导出 MD/TXT，返回 (content, filename)。"""
        novel = self.get_novel(novel_id)
        if not novel:
            raise ValueError("小说不存在")

        lines: list[str] = []
        if fmt == "md":
            lines.append(f"# {novel.title or '未命名小说'}")
            lines.append("")
            if novel.synopsis:
                lines.append(f"> {novel.synopsis}")
                lines.append("")
            for ch in sorted(novel.chapters, key=lambda c: c.index):
                if ch.status != "completed":
                    continue
                lines.append(f"## 第{ch.index}章 {ch.title}")
                lines.append("")
                lines.append(ch.content)
                lines.append("")
            ext = "md"
        else:
            lines.append(novel.title or "未命名小说")
            lines.append("=" * 40)
            if novel.synopsis:
                lines.append(novel.synopsis)
                lines.append("")
            for ch in sorted(novel.chapters, key=lambda c: c.index):
                if ch.status != "completed":
                    continue
                lines.append(f"第{ch.index}章 {ch.title}")
                lines.append("-" * 20)
                lines.append(ch.content)
                lines.append("")
            ext = "txt"

        safe_title = (novel.title or "novel").replace("/", "_")[:50]
        return "\n".join(lines), f"{safe_title}.{ext}"

    def to_response(self, novel: Novel) -> NovelResponse:
        chapters = sorted(novel.chapters or [], key=lambda c: c.index)
        bible = self._bible_for_response(novel.id, parse_bible(novel.bible_json))
        return NovelResponse(
            id=novel.id,
            premise=novel.premise,
            genre=novel.genre,
            title=novel.title,
            synopsis=novel.synopsis,
            bible_json=json.dumps(bible, ensure_ascii=False),
            status=novel.status,
            progress=novel.progress,
            error=novel.error,
            created_at=novel.created_at,
            chapters=[NovelChapterResponse.model_validate(c) for c in chapters],
        )

    def _bible_for_response(self, novel_id: str, bible: dict) -> dict:
        if not bible.get("meta", {}).get("outline_in_db"):
            return bible
        from app.services.novel_outline_service import NovelOutlineService

        total = int(bible.get("meta", {}).get("total_chapters") or 500)
        return NovelOutlineService(self._db).merge_into_bible(
            bible, novel_id, max_items=min(total, 500)
        )

    _ACTIVE_STATUSES = frozenset({"pending", "planning", "writing"})

    def delete_novel(self, novel_id: str) -> bool:
        """删除小说及关联 outline/实体/框架/Chroma。"""
        novel = self.get_novel(novel_id)
        if not novel:
            return False
        if novel.status in self._ACTIVE_STATUSES:
            raise ValueError("进行中的小说不可删除")

        from app.models.novel_entity import NovelEntity
        from app.models.novel_framework_item import NovelFrameworkItem
        from app.services.novel_outline_service import NovelOutlineService

        NovelOutlineService(self._db).delete_all(novel_id)
        self._db.query(NovelEntity).filter(NovelEntity.novel_id == novel_id).delete()
        self._db.query(NovelFrameworkItem).filter(NovelFrameworkItem.novel_id == novel_id).delete()
        try:
            from app.services.novel_memory_service import NovelMemoryService

            NovelMemoryService(self._db).drop_collection(novel_id)
        except Exception:
            pass
        self._db.delete(novel)
        self._db.commit()
        return True

    def to_list_item(self, novel: Novel) -> NovelListItem:
        return NovelListItem(
            id=novel.id,
            premise=novel.premise,
            genre=novel.genre,
            title=novel.title or novel.premise[:30],
            status=novel.status,
            progress=novel.progress,
            created_at=novel.created_at,
        )

    @staticmethod
    def genre_display(genre: str) -> str:
        return genre_label(genre)
