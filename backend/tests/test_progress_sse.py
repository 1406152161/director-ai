# @author zhangzhihao
"""SSE 进度推送测试。"""

import json

import pytest
from app.services.progress_hub import ProgressHub, progress_snapshot


@pytest.mark.asyncio
async def test_progress_hub_publish_and_terminal():
    hub = ProgressHub()

    async def collect() -> list[dict]:
        items: list[dict] = []
        async for event in hub.subscribe("project", "proj-1"):
            items.append(event)
            if event.get("done"):
                break
        return items

    task = __import__("asyncio").create_task(collect())
    await __import__("asyncio").sleep(0.05)
    hub.publish_nowait("project", "proj-1", status="scripting", progress=15)
    hub.publish_nowait("project", "proj-1", status="completed", progress=100)
    events = await __import__("asyncio").wait_for(task, timeout=2.0)
    assert events[0]["status"] == "scripting"
    assert events[-1]["status"] == "completed"
    assert events[-1]["done"] is True


def test_progress_snapshot_terminal_states():
    done = progress_snapshot("novel", status="planned", progress=100, error=None)
    assert done["done"] is True
    active = progress_snapshot("project", status="imaging", progress=40, error=None)
    assert active["done"] is False


def test_project_events_sse_initial_frame(client):
    create_resp = client.post(
        "/api/projects",
        json={"story": "SSE 测试", "style": "vlog", "duration": 15, "aspect_ratio": "9:16"},
    )
    project_id = create_resp.json()["id"]

    with client.stream("GET", f"/api/projects/{project_id}/events") as response:
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")
        line = next(response.iter_lines())
        assert line.startswith("data: ")
        payload = json.loads(line.removeprefix("data: "))
        assert payload["type"] == "progress"
        assert payload["status"] in {"pending", "scripting", "completed", "failed"}
        assert isinstance(payload["progress"], int)


def test_project_events_not_found(client):
    resp = client.get("/api/projects/missing-id/events")
    assert resp.status_code == 404


def test_novel_events_sse_initial_frame(client):
    create_resp = client.post(
        "/api/novels",
        json={"premise": "SSE 小说", "genre": "xuanhuan", "target_chapters": 10},
    )
    novel_id = create_resp.json()["id"]

    with client.stream("GET", f"/api/novels/{novel_id}/events") as response:
        assert response.status_code == 200
        line = next(response.iter_lines())
        payload = json.loads(line.removeprefix("data: "))
        assert payload["type"] == "progress"
        assert payload["status"] in {"pending", "planning", "planned", "failed"}


def test_service_emit_updates_subscribers():
    """同步 emit 可被 hub 队列接收（与 SSE 生成器同进程）。"""
    hub = ProgressHub()
    received: list[dict] = []

    async def drain():
        async for event in hub.subscribe("project", "p-sync"):
            if event.get("type") == "heartbeat":
                continue
            received.append(event)
            if event.get("done"):
                break

    loop = __import__("asyncio").new_event_loop()
    task = loop.create_task(drain())
    loop.run_until_complete(__import__("asyncio").sleep(0.05))
    hub.publish_nowait("project", "p-sync", status="imaging", progress=35)
    hub.publish_nowait("project", "p-sync", status="completed", progress=100)
    loop.run_until_complete(__import__("asyncio").wait_for(task, timeout=2))
    loop.close()
    assert received[0]["status"] == "imaging"
    assert received[-1]["done"] is True
