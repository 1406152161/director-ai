# @author zhangzhihao
"""小说相关 Pydantic 模型。"""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class NovelCreate(BaseModel):
    premise: str = Field(..., min_length=1, max_length=500, description="一句话创意")
    genre: str = Field(..., description="题材 key：xuanhuan/dushi/xuanyi/tianai/kehuan")
    target_chapters: int | None = Field(
        default=None,
        ge=8,
        le=10000,
        description="目标章数，留空由 AI 建议；AI 可在目标±200 内定最终章数",
    )

    @field_validator("target_chapters", mode="before")
    @classmethod
    def empty_target_to_none(cls, v: object) -> int | None:
        if v == "" or v is None:
            return None
        return int(v)  # type: ignore[arg-type]


class NovelChapterResponse(BaseModel):
    id: str
    index: int
    title: str
    content: str
    summary: str
    word_count: int
    status: str
    validation_status: str = "pending"
    validation_score: int = 0
    validation_issues: str = "[]"

    model_config = {"from_attributes": True}


class NovelResponse(BaseModel):
    id: str
    premise: str
    genre: str
    title: str
    synopsis: str
    bible_json: str
    status: str
    progress: int = 0
    error: str | None = None
    created_at: datetime | None = None
    chapters: list[NovelChapterResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class NovelListItem(BaseModel):
    id: str
    premise: str
    genre: str
    title: str
    status: str
    progress: int = 0
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class NovelChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)


class NovelWriteRequest(BaseModel):
    write_count: int = Field(default=1, ge=1, le=20, description="本次撰写章数")


class NovelBiblePatch(BaseModel):
    """结构化更新 Story Bible 分区（Q1-C 表单编辑）。"""

    world: str | None = None
    power_system: str | None = None
    characters: list[dict] | None = None
    items: list[dict] | None = None
    outline: list[dict] | None = None
    volumes: list[dict] | None = None
    foreshadowing: list[dict] | None = None


class NovelChatResponse(BaseModel):
    reply: str
    novel: NovelResponse
