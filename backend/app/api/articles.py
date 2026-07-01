# @author zhangzhihao
"""图文 API。"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_auth_context, optional_owner_id
from app.core.config import get_settings
from app.core.database import get_db
from app.schemas.article import ArticleCreate, ArticleListItem, ArticleResponse
from app.services.article_service import ArticleService

router = APIRouter(prefix="/articles", tags=["articles"])


def _assert_owner(article, owner_id: str | None) -> None:
    if not get_settings().auth_enabled or owner_id is None:
        return
    if article.owner_id != owner_id:
        raise HTTPException(status_code=404, detail="图文不存在")


@router.get("", response_model=list[ArticleListItem])
async def list_articles(
    db: Session = Depends(get_db),
    owner_id: str | None = Depends(optional_owner_id),
) -> list[ArticleListItem]:
    svc = ArticleService(db)
    return [svc.to_list_item(a) for a in svc.list_for_owner(owner_id)]


@router.post("", response_model=ArticleResponse, status_code=201)
async def create_article(
    body: ArticleCreate,
    db: Session = Depends(get_db),
    ctx=Depends(get_auth_context),
) -> ArticleResponse:
    if get_settings().auth_enabled and ctx is None:
        raise HTTPException(status_code=401, detail="未登录")
    owner_id = ctx.user_id if ctx else None
    article = ArticleService(db).create(body, owner_id=owner_id)
    return ArticleService.to_response(article)


@router.get("/{article_id}", response_model=ArticleResponse)
async def get_article(
    article_id: str,
    db: Session = Depends(get_db),
    owner_id: str | None = Depends(optional_owner_id),
) -> ArticleResponse:
    svc = ArticleService(db)
    article = svc.get(article_id)
    if not article:
        raise HTTPException(status_code=404, detail="图文不存在")
    _assert_owner(article, owner_id)
    return svc.to_response(article)


@router.delete("/{article_id}", status_code=204)
async def delete_article(
    article_id: str,
    db: Session = Depends(get_db),
    owner_id: str | None = Depends(optional_owner_id),
) -> None:
    svc = ArticleService(db)
    article = svc.get(article_id)
    if not article:
        raise HTTPException(status_code=404, detail="图文不存在")
    _assert_owner(article, owner_id)
    svc.delete(article_id)
