# @author zhangzhihao
"""导演设定资产 ORM 模型（角色 / 场景 / 道具）。"""

import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Asset(Base):
    """跨镜头复用的设定参考图。"""

    __tablename__ = "assets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), nullable=False)
    asset_type: Mapped[str] = mapped_column(String(16), nullable=False)
    asset_key: Mapped[str] = mapped_column(String(64), nullable=False)
    name_cn: Mapped[str] = mapped_column(String(128), default="")
    description_en: Mapped[str] = mapped_column(Text, default="")
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="pending")

    project: Mapped["Project"] = relationship("Project", back_populates="assets")
