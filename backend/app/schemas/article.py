# @author zhangzhihao
"""图文 API Schema。"""

from pydantic import BaseModel, Field


class ArticleCreate(BaseModel):
    topic: str = Field(min_length=1, max_length=2000)
    platform: str = Field(default="xiaohongshu", pattern="^(xiaohongshu|wechat|weibo|general)$")
    tone: str = Field(default="friendly", max_length=32)


class ArticleResponse(BaseModel):
    id: str
    topic: str
    platform: str
    tone: str
    status: str
    title: str
    body_md: str
    error: str | None
    created_at: str | None


class ArticleListItem(BaseModel):
    id: str
    topic: str
    platform: str
    status: str
    title: str
    created_at: str | None
