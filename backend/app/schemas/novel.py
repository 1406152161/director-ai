# @author zhangzhihao
"""小说相关 Pydantic 模型。"""

from datetime import datetime

from pydantic import BaseModel, Field


class NovelCreate(BaseModel):
    premise: str = Field(..., min_length=1, max_length=500, description="一句话创意")
    genre: str = Field(..., description="题材 key：xuanhuan/dushi/xuanyi/tianai/kehuan")


class NovelChapterResponse(BaseModel):
    id: str
    index: int
    title: str
    content: str
    summary: str
    word_count: int
    status: str

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


class NovelChatResponse(BaseModel):
    reply: str
    novel: NovelResponse
