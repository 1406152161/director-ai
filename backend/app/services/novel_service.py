# @author zhangzhihao
"""小说 CRUD、导出与 Story Bible 持久化。"""

import json

from sqlalchemy.orm import Session, joinedload

from app.models.novel import Novel, NovelChapter
from app.novel.prompts import VALID_GENRES, genre_label
from app.schemas.novel import NovelCreate, NovelListItem, NovelResponse, NovelChapterResponse


class NovelService:
    """小说业务服务。"""

    def __init__(self, db: Session) -> None:
        self._db = db

    def create_novel(self, body: NovelCreate) -> Novel:
        if body.genre not in VALID_GENRES:
            raise ValueError(f"不支持的题材: {body.genre}")
        novel = Novel(
            premise=body.premise,
            genre=body.genre,
            status="pending",
            progress=0,
            bible_json="{}",
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

    def list_novels(self) -> list[Novel]:
        return self._db.query(Novel).order_by(Novel.created_at.desc()).all()

    def update_status(self, novel_id: str, status: str, progress: int | None = None) -> None:
        novel = self._db.query(Novel).filter(Novel.id == novel_id).first()
        if not novel:
            return
        novel.status = status
        if progress is not None:
            novel.progress = progress
        self._db.commit()

    def set_failed(self, novel_id: str, error: str) -> None:
        novel = self._db.query(Novel).filter(Novel.id == novel_id).first()
        if not novel:
            return
        novel.status = "failed"
        novel.error = error
        self._db.commit()

    def apply_plan(self, novel_id: str, plan: dict) -> None:
        """落库规划结果并初始化 Story Bible。"""
        novel = self._db.query(Novel).filter(Novel.id == novel_id).first()
        if not novel:
            return

        bible = {
            "world": plan.get("world", ""),
            "facts": [],
            "characters": [
                {
                    "name": c.get("name", ""),
                    "role": c.get("role", ""),
                    "traits": c.get("profile") or c.get("traits", ""),
                }
                for c in plan.get("characters", [])
            ],
            "outline": plan.get("outline", []),
        }
        novel.title = plan.get("title", "") or novel.title
        novel.synopsis = plan.get("synopsis", "") or novel.synopsis
        novel.bible_json = json.dumps(bible, ensure_ascii=False)
        self._db.commit()

    def save_bible(self, novel_id: str, bible: dict) -> None:
        novel = self._db.query(Novel).filter(Novel.id == novel_id).first()
        if not novel:
            return
        novel.bible_json = json.dumps(bible, ensure_ascii=False)
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
    ) -> None:
        chapter = self._db.query(NovelChapter).filter(NovelChapter.id == chapter_id).first()
        if not chapter:
            return
        chapter.title = title
        chapter.content = content
        chapter.summary = summary
        chapter.word_count = word_count
        chapter.status = status
        self._db.commit()

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
        return NovelResponse(
            id=novel.id,
            premise=novel.premise,
            genre=novel.genre,
            title=novel.title,
            synopsis=novel.synopsis,
            bible_json=novel.bible_json,
            status=novel.status,
            progress=novel.progress,
            error=novel.error,
            created_at=novel.created_at,
            chapters=[NovelChapterResponse.model_validate(c) for c in chapters],
        )

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
