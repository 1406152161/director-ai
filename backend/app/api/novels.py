# @author zhangzhihao
"""小说 API 路由。"""

from urllib.parse import quote

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.api.deps import get_auth_context, optional_owner_id
from app.api.streaming import progress_event_response
from app.core.config import get_settings
from app.core.database import get_db
from app.schemas.novel import (
    NovelBiblePatch,
    NovelChatRequest,
    NovelChatResponse,
    NovelCreate,
    NovelListItem,
    NovelResponse,
    NovelWriteRequest,
)
from app.services.novel_chat_service import NovelChatService
from app.services.novel_outline_service import NovelOutlineService
from app.services.novel_service import NovelService
from app.services.task_dispatch import (
    enqueue_approve_chapter,
    enqueue_novel_generation,
    enqueue_novel_next_chapter,
    enqueue_novel_start_writing,
    enqueue_replan_novel,
    enqueue_rewrite_chapter,
)

router = APIRouter(prefix="/novels", tags=["novels"])


@router.get("", response_model=list[NovelListItem])
async def list_novels(
    db: Session = Depends(get_db),
    owner_id: str | None = Depends(optional_owner_id),
) -> list[NovelListItem]:
    svc = NovelService(db)
    return [svc.to_list_item(n) for n in svc.list_novels(owner_id)]


@router.post("", response_model=NovelResponse, status_code=201)
async def create_novel(
    body: NovelCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    ctx=Depends(get_auth_context),
) -> NovelResponse:
    svc = NovelService(db)
    if get_settings().auth_enabled and ctx is None:
        raise HTTPException(status_code=401, detail="未登录")
    try:
        novel = svc.create_novel(body, owner_id=ctx.user_id if ctx else None)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    enqueue_novel_generation(background_tasks, novel.id)
    return svc.to_response(novel)


@router.get("/{novel_id}", response_model=NovelResponse)
async def get_novel(novel_id: str, db: Session = Depends(get_db)) -> NovelResponse:
    svc = NovelService(db)
    novel = svc.get_novel(novel_id)
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")
    return svc.to_response(novel)


@router.delete("/{novel_id}", status_code=204)
async def delete_novel(novel_id: str, db: Session = Depends(get_db)) -> None:
    svc = NovelService(db)
    novel = svc.get_novel(novel_id)
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")
    try:
        svc.delete_novel(novel_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


def _novel_progress_snapshot(db: Session, novel_id: str) -> tuple[str, int, str | None] | None:
    svc = NovelService(db)
    novel = svc.get_novel(novel_id)
    if not novel:
        return None
    return novel.status, novel.progress, novel.error


@router.get("/{novel_id}/events")
async def novel_progress_events(novel_id: str, db: Session = Depends(get_db)):
    return progress_event_response("novel", novel_id, db, load_snapshot=_novel_progress_snapshot)


@router.get("/{novel_id}/outline")
async def list_novel_outline(
    novel_id: str,
    from_chapter: int = Query(1, ge=1, alias="from"),
    to_chapter: int | None = Query(None, ge=1, alias="to"),
    detail_level: str | None = Query(None, pattern="^(skeleton|detailed)$"),
    detail: str | None = Query(None, pattern="^(skeleton|detailed)$"),
    db: Session = Depends(get_db),
) -> list[dict]:
    svc = NovelService(db)
    novel = svc.get_novel(novel_id)
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")
    outline_svc = NovelOutlineService(db)
    level = detail_level or detail
    rows = outline_svc.list_range(novel_id, from_chapter, to_chapter, level)
    return [NovelOutlineService._to_dict(r) for r in rows]


@router.post("/{novel_id}/retry-plan", response_model=NovelResponse)
async def retry_novel_plan(
    novel_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> NovelResponse:
    svc = NovelService(db)
    novel = svc.get_novel(novel_id)
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")
    if novel.status not in ("failed", "pending", "planning"):
        raise HTTPException(status_code=409, detail="当前状态不可重新规划")
    svc.reset_for_planning(novel_id)
    enqueue_novel_generation(background_tasks, novel_id)
    novel = svc.get_novel(novel_id)
    return svc.to_response(novel)


@router.post("/{novel_id}/chapters/next", response_model=NovelResponse)
async def continue_novel(
    novel_id: str,
    body: NovelWriteRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> NovelResponse:
    svc = NovelService(db)
    novel = svc.get_novel(novel_id)
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")
    if novel.status == "writing":
        raise HTTPException(status_code=409, detail="正在写作中，请稍后再试")
    if novel.status == "planned":
        raise HTTPException(status_code=409, detail="请先确认大纲并开始写作")
    if novel.status == "review_required" or svc.has_blocking_review(novel_id):
        raise HTTPException(status_code=409, detail="存在待复核章节，请先处理后再续写")
    enqueue_novel_next_chapter(background_tasks, novel_id, body.write_count)
    svc.update_status(novel_id, "writing", novel.progress)
    novel = svc.get_novel(novel_id)
    return svc.to_response(novel)


@router.post("/{novel_id}/start-writing", response_model=NovelResponse)
async def start_writing_novel(
    novel_id: str,
    body: NovelWriteRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> NovelResponse:
    svc = NovelService(db)
    novel = svc.get_novel(novel_id)
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")
    if novel.status != "planned":
        raise HTTPException(status_code=409, detail="当前状态不可开始写作")
    enqueue_novel_start_writing(background_tasks, novel_id, body.write_count)
    novel = svc.get_novel(novel_id)
    return svc.to_response(novel)


@router.patch("/{novel_id}/bible", response_model=NovelResponse)
async def patch_novel_bible(
    novel_id: str,
    body: NovelBiblePatch,
    db: Session = Depends(get_db),
) -> NovelResponse:
    svc = NovelService(db)
    novel = svc.get_novel(novel_id)
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")
    patch = body.model_dump(exclude_unset=True)
    if not patch:
        raise HTTPException(status_code=400, detail="无更新内容")
    try:
        svc.patch_bible(novel_id, patch)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
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
    svc.sync_bible_indexes(novel_id, merged)
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


@router.post("/{novel_id}/chapters/{chapter_index}/approve", response_model=NovelResponse)
async def approve_chapter(
    novel_id: str,
    chapter_index: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> NovelResponse:
    svc = NovelService(db)
    novel = svc.get_novel(novel_id)
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")
    chapter = svc.get_chapter(novel_id, chapter_index)
    if not chapter or chapter.status != "needs_review":
        raise HTTPException(status_code=409, detail="该章节不可放行")
    enqueue_approve_chapter(background_tasks, novel_id, chapter_index)
    return svc.to_response(novel)


@router.post("/{novel_id}/chapters/{chapter_index}/rewrite", response_model=NovelResponse)
async def rewrite_chapter(
    novel_id: str,
    chapter_index: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> NovelResponse:
    svc = NovelService(db)
    novel = svc.get_novel(novel_id)
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")
    if novel.status == "writing":
        raise HTTPException(status_code=409, detail="正在写作中，请稍后再试")
    chapter = svc.get_chapter(novel_id, chapter_index)
    if not chapter or chapter.status != "needs_review":
        raise HTTPException(status_code=409, detail="该章节不可重写")
    enqueue_rewrite_chapter(background_tasks, novel_id, chapter_index)
    svc.update_status(novel_id, "writing", novel.progress)
    novel = svc.get_novel(novel_id)
    return svc.to_response(novel)


@router.post("/{novel_id}/replan", response_model=NovelResponse)
async def replan_novel(
    novel_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> NovelResponse:
    svc = NovelService(db)
    novel = svc.get_novel(novel_id)
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")
    if novel.status == "writing":
        raise HTTPException(status_code=409, detail="正在写作中")
    enqueue_replan_novel(background_tasks, novel_id)
    return svc.to_response(novel)
