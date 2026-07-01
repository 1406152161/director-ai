# @author zhangzhihao
"""章级大纲条目 ORM（L1 骨架 + L2 详细）。"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


class NovelOutlineItem(Base):
    """全书章纲 SSOT；skeleton 仅 title+summary，detailed 含 hook。"""

    __tablename__ = "novel_outline_items"
    __table_args__ = (UniqueConstraint("novel_id", "chapter_index", name="uq_novel_outline_index"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    novel_id: Mapped[str] = mapped_column(String(36), ForeignKey("novels.id"), nullable=False)
    chapter_index: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(256), default="")
    summary: Mapped[str] = mapped_column(Text, default="")
    hook: Mapped[str] = mapped_column(Text, default="")
    arc_id: Mapped[str] = mapped_column(String(64), default="")
    volume_id: Mapped[str] = mapped_column(String(64), default="")
    detail_level: Mapped[str] = mapped_column(String(16), default="skeleton")
    locked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
