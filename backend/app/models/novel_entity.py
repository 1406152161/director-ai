# @author zhangzhihao
"""小说实体注册表 ORM。"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


class NovelEntity(Base):
    """人物/道具/地点/时间线等结构化实体。"""

    __tablename__ = "novel_entities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    novel_id: Mapped[str] = mapped_column(String(36), ForeignKey("novels.id"), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(32), nullable=False)
    entity_key: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(128), default="")
    data_json: Mapped[str] = mapped_column(Text, default="{}")
    status: Mapped[str] = mapped_column(String(16), default="confirmed")
    last_chapter_index: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
