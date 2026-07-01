# @author zhangzhihao
"""进度事件总线：内存 fan-out + Redis pub/sub（Celery 跨进程）。"""

from __future__ import annotations

import asyncio
import json
import logging
from collections import defaultdict
from collections.abc import AsyncIterator
from typing import Any, Literal

logger = logging.getLogger(__name__)

ResourceKind = Literal["project", "novel"]
PROGRESS_CHANNEL = "director:progress"

TERMINAL_PROJECT: frozenset[str] = frozenset({"completed", "failed"})
TERMINAL_NOVEL: frozenset[str] = frozenset({"completed", "failed", "planned", "review_required"})


def _is_terminal(kind: ResourceKind, status: str) -> bool:
    terminal = TERMINAL_PROJECT if kind == "project" else TERMINAL_NOVEL
    return status in terminal


def _build_payload(
    kind: ResourceKind,
    *,
    status: str,
    progress: int,
    error: str | None,
) -> dict[str, Any]:
    return {
        "type": "progress",
        "status": status,
        "progress": progress,
        "error": error,
        "done": _is_terminal(kind, status),
    }


class ProgressHub:
    """按资源维度 fan-out；Redis 广播供 Celery Worker → API SSE。"""

    def __init__(self) -> None:
        self._queues: dict[
            tuple[ResourceKind, str], list[asyncio.Queue[dict[str, Any]]]
        ] = defaultdict(list)
        self._lock = asyncio.Lock()
        self._redis = None
        self._redis_enabled = False
        self._init_redis()

    def _init_redis(self) -> None:
        try:
            import redis

            from app.core.config import get_settings

            client = redis.from_url(get_settings().redis_url, socket_connect_timeout=0.3)
            client.ping()
            self._redis = client
            self._redis_enabled = True
        except Exception as exc:
            logger.debug("ProgressHub Redis 不可用，仅本进程内存广播: %s", exc)

    def publish_nowait(
        self,
        kind: ResourceKind,
        resource_id: str,
        *,
        status: str,
        progress: int,
        error: str | None = None,
    ) -> None:
        payload = _build_payload(kind, status=status, progress=progress, error=error)
        key = (kind, resource_id)
        for queue in list(self._queues.get(key, [])):
            try:
                queue.put_nowait(payload)
            except asyncio.QueueFull:
                pass

        if self._redis_enabled and self._redis:
            envelope = json.dumps(
                {"kind": kind, "resource_id": resource_id, "payload": payload},
                ensure_ascii=False,
            )
            try:
                self._redis.publish(PROGRESS_CHANNEL, envelope)
            except Exception as exc:
                logger.warning("ProgressHub Redis publish 失败: %s", exc)

    async def _redis_listener(
        self,
        kind: ResourceKind,
        resource_id: str,
        queue: asyncio.Queue[dict[str, Any]],
        stop: asyncio.Event,
    ) -> None:
        try:
            import redis.asyncio as aioredis

            from app.core.config import get_settings

            client = aioredis.from_url(get_settings().redis_url)
            pubsub = client.pubsub()
            await pubsub.subscribe(PROGRESS_CHANNEL)
            while not stop.is_set():
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=25.0)
                if message is None:
                    continue
                if message.get("type") != "message":
                    continue
                raw = message.get("data")
                if isinstance(raw, bytes):
                    raw = raw.decode("utf-8")
                data = json.loads(raw)
                if data.get("kind") == kind and data.get("resource_id") == resource_id:
                    payload = data.get("payload") or {}
                    await queue.put(payload)
                    if payload.get("done"):
                        break
            await pubsub.unsubscribe(PROGRESS_CHANNEL)
            await pubsub.close()
            await client.close()
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.debug("ProgressHub Redis listener 结束: %s", exc)

    async def subscribe(
        self, kind: ResourceKind, resource_id: str
    ) -> AsyncIterator[dict[str, Any]]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=64)
        key = (kind, resource_id)
        stop = asyncio.Event()
        redis_task: asyncio.Task[None] | None = None

        async with self._lock:
            self._queues[key].append(queue)

        if self._redis_enabled:
            redis_task = asyncio.create_task(self._redis_listener(kind, resource_id, queue, stop))

        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=25.0)
                except TimeoutError:
                    yield {"type": "heartbeat"}
                    continue
                yield event
                if event.get("done"):
                    break
        finally:
            stop.set()
            if redis_task:
                redis_task.cancel()
                try:
                    await redis_task
                except asyncio.CancelledError:
                    pass
            async with self._lock:
                subs = self._queues.get(key, [])
                if queue in subs:
                    subs.remove(queue)


_hub = ProgressHub()


def get_progress_hub() -> ProgressHub:
    return _hub


def emit_progress(
    kind: ResourceKind,
    resource_id: str,
    *,
    status: str,
    progress: int,
    error: str | None = None,
) -> None:
    get_progress_hub().publish_nowait(
        kind,
        resource_id,
        status=status,
        progress=progress,
        error=error,
    )


def progress_snapshot(
    kind: ResourceKind,
    *,
    status: str,
    progress: int,
    error: str | None = None,
) -> dict[str, Any]:
    return _build_payload(kind, status=status, progress=progress, error=error)


def format_sse(data: dict[str, Any]) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
