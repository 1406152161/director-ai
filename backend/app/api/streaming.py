# @author zhangzhihao
"""SSE 流式响应辅助。"""

from collections.abc import AsyncIterator, Callable

from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.services.progress_hub import ResourceKind, format_sse, get_progress_hub, progress_snapshot

SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}


async def stream_progress_events(
    kind: ResourceKind,
    resource_id: str,
    *,
    status: str,
    progress: int,
    error: str | None,
) -> AsyncIterator[str]:
    initial = progress_snapshot(kind, status=status, progress=progress, error=error)
    yield format_sse(initial)
    if initial.get("done"):
        return

    hub = get_progress_hub()
    async for event in hub.subscribe(kind, resource_id):
        yield format_sse(event)
        if event.get("type") == "progress" and event.get("done"):
            break


def progress_event_response(
    kind: ResourceKind,
    resource_id: str,
    db: Session,
    *,
    load_snapshot: Callable[[Session, str], tuple[str, int, str | None] | None],
) -> StreamingResponse:
    snapshot = load_snapshot(db, resource_id)
    if snapshot is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="资源不存在")

    status, progress, error = snapshot

    async def generator() -> AsyncIterator[str]:
        async for chunk in stream_progress_events(
            kind,
            resource_id,
            status=status,
            progress=progress,
            error=error,
        ):
            yield chunk

    return StreamingResponse(generator(), media_type="text/event-stream", headers=SSE_HEADERS)
