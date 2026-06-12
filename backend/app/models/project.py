# @author zhangzhihao
"""项目与分镜镜头 ORM 模型。"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Project(Base):
    """一次创作任务。"""

    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    story: Mapped[str] = mapped_column(Text, nullable=False)
    style: Mapped[str] = mapped_column(String(32), default="cinematic")
    duration: Mapped[int] = mapped_column(Integer, default=30)
    aspect_ratio: Mapped[str] = mapped_column(String(8), default="9:16")
    status: Mapped[str] = mapped_column(String(16), default="pending")
    progress: Mapped[int] = mapped_column(Integer, default=0)
    title: Mapped[str | None] = mapped_column(String(256), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    shots: Mapped[list["Shot"]] = relationship(
        "Shot", back_populates="project", cascade="all, delete-orphan", order_by="Shot.index"
    )


class Shot(Base):
    """分镜镜头。"""

    __tablename__ = "shots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), nullable=False)
    index: Mapped[int] = mapped_column(Integer, nullable=False)
    scene_cn: Mapped[str] = mapped_column(Text, default="")
    image_prompt_en: Mapped[str] = mapped_column(Text, default="")
    narration_cn: Mapped[str] = mapped_column(Text, default="")
    duration: Mapped[int] = mapped_column(Integer, default=4)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="pending")

    project: Mapped["Project"] = relationship("Project", back_populates="shots")
