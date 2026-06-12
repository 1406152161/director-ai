# @author zhangzhihao
"""项目相关 Pydantic 模型。"""

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    story: str = Field(..., min_length=1, max_length=200, description="创意描述")
    style: str = Field(default="cinematic", description="视觉风格")
    duration: int = Field(default=30, ge=5, le=300, description="目标时长（秒）")
    aspect_ratio: str = Field(default="16:9", description="版式比例")


class ProjectResponse(BaseModel):
    id: str
    story: str
    style: str
    duration: int
    aspect_ratio: str
    status: str
