# @author zhangzhihao
"""图文创作占位服务。"""

from sqlalchemy.orm import Session

from app.models.article import Article
from app.schemas.article import ArticleCreate, ArticleListItem, ArticleResponse

_PLATFORM_LABEL = {
    "xiaohongshu": "小红书",
    "wechat": "公众号",
    "weibo": "微博",
    "general": "通用",
}


class ArticleService:
    """图文任务 CRUD（当前为预览占位）。"""

    def __init__(self, db: Session) -> None:
        self._db = db

    def create(self, body: ArticleCreate, owner_id: str | None = None) -> Article:
        platform_label = _PLATFORM_LABEL.get(body.platform, body.platform)
        title = f"「{body.topic[:24]}」{platform_label}图文预览"
        body_md = (
            f"# {title}\n\n"
            f"> 平台：{platform_label} · 语气：{body.tone}\n\n"
            f"## 导语\n\n"
            f"围绕「{body.topic}」的图文内容将在此生成。\n\n"
            f"## 正文（占位）\n\n"
            f"- 要点一：与主题相关的钩子句\n"
            f"- 要点二：场景化描述\n"
            f"- 要点三：行动号召\n\n"
            f"---\n\n"
            f"*完整图文生成能力将在后续版本接入 LLM + 配图 Pipeline。*"
        )
        article = Article(
            topic=body.topic.strip(),
            platform=body.platform,
            tone=body.tone,
            status="preview",
            title=title,
            body_md=body_md,
            owner_id=owner_id,
        )
        self._db.add(article)
        self._db.commit()
        self._db.refresh(article)
        return article

    def get(self, article_id: str) -> Article | None:
        return self._db.query(Article).filter(Article.id == article_id).first()

    def list_for_owner(self, owner_id: str | None) -> list[Article]:
        q = self._db.query(Article).order_by(Article.created_at.desc())
        if owner_id:
            q = q.filter(Article.owner_id == owner_id)
        return q.all()

    def delete(self, article_id: str) -> bool:
        article = self.get(article_id)
        if not article:
            return False
        self._db.delete(article)
        self._db.commit()
        return True

    @staticmethod
    def to_response(article: Article) -> ArticleResponse:
        return ArticleResponse(
            id=article.id,
            topic=article.topic,
            platform=article.platform,
            tone=article.tone,
            status=article.status,
            title=article.title,
            body_md=article.body_md,
            error=article.error,
            created_at=article.created_at.isoformat() if article.created_at else None,
        )

    @staticmethod
    def to_list_item(article: Article) -> ArticleListItem:
        return ArticleListItem(
            id=article.id,
            topic=article.topic,
            platform=article.platform,
            status=article.status,
            title=article.title,
            created_at=article.created_at.isoformat() if article.created_at else None,
        )
