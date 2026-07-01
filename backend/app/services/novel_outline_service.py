# @author zhangzhihao
"""章级大纲 DB 服务：L1 骨架 / L2 详细 / 导出到 Bible。"""

from typing import Any

from sqlalchemy.orm import Session

from app.models.novel_outline_item import NovelOutlineItem


class NovelOutlineService:
    """outline SSOT，替代 bible_json 中存千章大纲。"""

    def __init__(self, db: Session) -> None:
        self._db = db

    def count_by_level(self, novel_id: str, detail_level: str | None = None) -> int:
        q = self._db.query(NovelOutlineItem).filter(NovelOutlineItem.novel_id == novel_id)
        if detail_level:
            q = q.filter(NovelOutlineItem.detail_level == detail_level)
        return q.count()

    def list_range(
        self,
        novel_id: str,
        chapter_from: int = 1,
        chapter_to: int | None = None,
        detail_level: str | None = None,
    ) -> list[NovelOutlineItem]:
        q = (
            self._db.query(NovelOutlineItem)
            .filter(
                NovelOutlineItem.novel_id == novel_id,
                NovelOutlineItem.chapter_index >= chapter_from,
            )
            .order_by(NovelOutlineItem.chapter_index)
        )
        if chapter_to is not None:
            q = q.filter(NovelOutlineItem.chapter_index <= chapter_to)
        if detail_level:
            q = q.filter(NovelOutlineItem.detail_level == detail_level)
        return q.all()

    def get_chapter(self, novel_id: str, chapter_index: int) -> NovelOutlineItem | None:
        return (
            self._db.query(NovelOutlineItem)
            .filter(
                NovelOutlineItem.novel_id == novel_id,
                NovelOutlineItem.chapter_index == chapter_index,
            )
            .first()
        )

    def upsert_batch(
        self,
        novel_id: str,
        items: list[dict[str, Any]],
        *,
        detail_level: str,
        locked: bool = False,
    ) -> None:
        for raw in items:
            idx = int(raw.get("index", 0))
            if idx < 1:
                continue
            row = self.get_chapter(novel_id, idx)
            if row is None:
                row = NovelOutlineItem(
                    novel_id=novel_id,
                    chapter_index=idx,
                    detail_level=detail_level,
                )
                self._db.add(row)
            row.title = raw.get("title") or row.title or f"第{idx}章"
            row.summary = raw.get("summary") or row.summary or ""
            if detail_level == "detailed":
                row.hook = raw.get("hook") or row.hook or ""
                row.detail_level = "detailed"
            row.arc_id = str(raw.get("arc_id") or row.arc_id or "")
            row.volume_id = str(raw.get("volume_id") or row.volume_id or "")
            if locked:
                row.locked = True
        self._db.commit()

    def delete_all(self, novel_id: str) -> None:
        self._db.query(NovelOutlineItem).filter(NovelOutlineItem.novel_id == novel_id).delete()
        self._db.commit()

    def anchor_items(self, novel_id: str, before_index: int, count: int = 3) -> list[dict[str, Any]]:
        """衔接锚点：before_index 之前的若干章。"""
        start = max(1, before_index - count)
        rows = self.list_range(novel_id, start, before_index - 1)
        return [self._to_dict(r) for r in rows]

    def locked_skeleton_prefix(self, novel_id: str, before_index: int) -> list[dict[str, Any]]:
        if before_index <= 1:
            return []
        rows = self.list_range(novel_id, 1, before_index - 1)
        return [self._to_dict(r) for r in rows]

    def to_bible_outline(
        self,
        novel_id: str,
        chapter_from: int = 1,
        chapter_to: int | None = None,
    ) -> list[dict[str, Any]]:
        rows = self.list_range(novel_id, chapter_from, chapter_to)
        return [self._to_dict(r) for r in rows]

    def merge_into_bible(self, bible: dict[str, Any], novel_id: str, max_items: int = 500) -> dict[str, Any]:
        """将 DB outline 合并进 bible 供前端/API（默认最多 500 条）。"""
        rows = self.list_range(novel_id, 1, max_items)
        bible = dict(bible)
        bible["outline"] = [self._to_dict(r) for r in rows]
        return bible

    @staticmethod
    def _to_dict(row: NovelOutlineItem) -> dict[str, Any]:
        return {
            "index": row.chapter_index,
            "title": row.title,
            "summary": row.summary,
            "hook": row.hook,
            "arc_id": row.arc_id,
            "volume_id": row.volume_id,
            "detail_level": row.detail_level,
        }

    @staticmethod
    def entry_for_writing(row: NovelOutlineItem | None, chapter_index: int) -> dict | None:
        if not row:
            return None
        return {
            "index": row.chapter_index,
            "title": row.title or f"第{chapter_index}章",
            "summary": row.summary,
            "hook": row.hook,
            "arc_id": row.arc_id,
            "volume_id": row.volume_id,
        }
