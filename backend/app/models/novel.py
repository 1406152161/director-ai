# @author zhangzhihao
"""小说与章节 ORM 模型。"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Novel(Base):
    """一本小说创作任务。"""

    __tablename__ = "novels"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    premise: Mapped[str] = mapped_column(Text, nullable=False)
    genre: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(String(256), default="")
    synopsis: Mapped[str] = mapped_column(Text, default="")
    bible_json: Mapped[str] = mapped_column(Text, default="{}")
    status: Mapped[str] = mapped_column(String(16), default="pending")
    progress: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    chapters: Mapped[list["NovelChapter"]] = relationship(
        "NovelChapter",
        back_populates="novel",
        cascade="all, delete-orphan",
        order_by="NovelChapter.index",
    )


class NovelChapter(Base):
    """小说章节。"""

    __tablename__ = "novel_chapters"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    novel_id: Mapped[str] = mapped_column(String(36), ForeignKey("novels.id"), nullable=False)
    index: Mapped[int] = mapped_column("index", Integer, nullable=False, quote=True)
    title: Mapped[str] = mapped_column(String(256), default="")
    content: Mapped[str] = mapped_column(Text, default="")
    summary: Mapped[str] = mapped_column(Text, default="")
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(16), default="pending")

    novel: Mapped["Novel"] = relationship("Novel", back_populates="chapters")
