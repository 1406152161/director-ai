# @author zhangzhihao
"""项目相关 Pydantic 模型。"""

from datetime import datetime

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    story: str = Field(..., min_length=1, max_length=200, description="创意描述")
    style: str = Field(default="cinematic", description="视觉风格")
    duration: int = Field(default=30, ge=5, le=300, description="目标时长（秒）")
    aspect_ratio: str = Field(default="9:16", description="版式比例")


class ShotResponse(BaseModel):
    id: str
    index: int
    scene_cn: str
    image_prompt_en: str
    motion_prompt_en: str = ""
    narration_cn: str
    duration: int
    image_url: str | None = None
    video_url: str | None = None
    audio_url: str | None = None
    clip_url: str | None = None
    clip_status: str = "pending"
    status: str

    model_config = {"from_attributes": True}


class AssetResponse(BaseModel):
    id: str
    asset_type: str
    asset_key: str
    name_cn: str
    description_en: str
    image_url: str | None = None
    status: str

    model_config = {"from_attributes": True}


class ProjectResponse(BaseModel):
    id: str
    story: str
    style: str
    duration: int
    aspect_ratio: str
    status: str
    progress: int = 0
    title: str | None = None
    error: str | None = None
    output_url: str | None = None
    created_at: datetime | None = None
    shots: list[ShotResponse] = Field(default_factory=list)
    assets: list[AssetResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class ProjectListItem(BaseModel):
    id: str
    story: str
    style: str
    duration: int
    aspect_ratio: str
    status: str
    progress: int = 0
    title: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
