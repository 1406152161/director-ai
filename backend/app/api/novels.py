# @author zhangzhihao
"""小说 API 路由。"""

from urllib.parse import quote

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.novel import (
    NovelChatRequest,
    NovelChatResponse,
    NovelCreate,
    NovelListItem,
    NovelResponse,
)
from app.services.novel_generation_service import run_novel_generation, run_novel_next_chapter
from app.services.novel_chat_service import NovelChatService
from app.services.novel_service import NovelService

router = APIRouter(prefix="/novels", tags=["novels"])


@router.get("", response_model=list[NovelListItem])
async def list_novels(db: Session = Depends(get_db)) -> list[NovelListItem]:
    svc = NovelService(db)
    return [svc.to_list_item(n) for n in svc.list_novels()]


@router.post("", response_model=NovelResponse, status_code=201)
async def create_novel(
    body: NovelCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> NovelResponse:
    svc = NovelService(db)
    try:
        novel = svc.create_novel(body)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    background_tasks.add_task(run_novel_generation, novel.id)
    return svc.to_response(novel)


@router.get("/{novel_id}", response_model=NovelResponse)
async def get_novel(novel_id: str, db: Session = Depends(get_db)) -> NovelResponse:
    svc = NovelService(db)
    novel = svc.get_novel(novel_id)
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")
    return svc.to_response(novel)


@router.post("/{novel_id}/chapters/next", response_model=NovelResponse)
async def continue_novel(
    novel_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> NovelResponse:
    svc = NovelService(db)
    novel = svc.get_novel(novel_id)
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")
    if novel.status == "writing":
        raise HTTPException(status_code=409, detail="正在写作中，请稍后再试")
    background_tasks.add_task(run_novel_next_chapter, novel_id)
    svc.update_status(novel_id, "writing", novel.progress)
    novel = svc.get_novel(novel_id)
    return svc.to_response(novel)


@router.post("/{novel_id}/chat", response_model=NovelChatResponse)
async def chat_novel(
    novel_id: str,
    body: NovelChatRequest,
    db: Session = Depends(get_db),
) -> NovelChatResponse:
    svc = NovelService(db)
    novel = svc.get_novel(novel_id)
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")

    chat_svc = NovelChatService()
    reply, merged = await chat_svc.chat(novel.bible_json, body.message)
    svc.save_bible(novel_id, merged)
    novel = svc.get_novel(novel_id)
    return NovelChatResponse(reply=reply, novel=svc.to_response(novel))


@router.get("/{novel_id}/export")
async def export_novel(
    novel_id: str,
    format: str = Query("md", pattern="^(md|txt)$"),
    db: Session = Depends(get_db),
) -> PlainTextResponse:
    svc = NovelService(db)
    novel = svc.get_novel(novel_id)
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")

    try:
        content, filename = svc.export_novel(novel_id, format)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    media_type = "text/markdown; charset=utf-8" if format == "md" else "text/plain; charset=utf-8"
    ascii_name = f"novel-{novel_id[:8]}.{format}"
    encoded_name = quote(filename)
    disposition = f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{encoded_name}"
    return PlainTextResponse(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": disposition},
    )
