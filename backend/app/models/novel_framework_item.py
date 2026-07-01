# @author zhangzhihao
"""小说框架记忆条目 ORM（大纲/伏笔/规则等）。"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, _utcnow


class NovelFrameworkItem(Base):
    """可检索的框架片段，SSOT 在 DB，Chroma 为索引。"""

    __tablename__ = "novel_framework_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    novel_id: Mapped[str] = mapped_column(String(36), ForeignKey("novels.id"), nullable=False)
    item_type: Mapped[str] = mapped_column(String(32), nullable=False)
    item_key: Mapped[str] = mapped_column(String(64), nullable=False)
    scope: Mapped[str] = mapped_column(String(16), default="global")
    chapter_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    chapter_from: Mapped[int | None] = mapped_column(Integer, nullable=True)
    chapter_to: Mapped[int | None] = mapped_column(Integer, nullable=True)
    title: Mapped[str] = mapped_column(String(256), default="")
    content: Mapped[str] = mapped_column(Text, default="")
    text_for_embed: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(16), default="confirmed")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
