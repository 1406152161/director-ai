# @author zhangzhihao
"""任务调度：BackgroundTasks vs Celery。"""

import time

import pytest

from app.core.config import get_settings


def test_use_celery_default_false():
    get_settings.cache_clear()
    settings = get_settings()
    assert settings.use_celery is False


def test_enqueue_video_uses_background_tasks_by_default(client, monkeypatch):
    calls: list[str] = []

    async def fake_run(project_id: str) -> None:
        calls.append(project_id)

    monkeypatch.setattr("app.services.task_dispatch.use_celery", lambda: False)
    monkeypatch.setattr("app.services.generation_service.run_generation", fake_run)

    resp = client.post(
        "/api/projects",
        json={"story": "dispatch 测试", "style": "vlog", "duration": 15, "aspect_ratio": "9:16"},
    )
    assert resp.status_code == 201
    project_id = resp.json()["id"]

    deadline = time.time() + 5.0
    while time.time() < deadline and project_id not in calls:
        time.sleep(0.05)
    assert project_id in calls


@pytest.fixture
def celery_eager(monkeypatch):
    monkeypatch.setenv("USE_CELERY", "true")
    get_settings.cache_clear()
    from app.tasks.celery_app import celery_app

    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True
    yield celery_app
    celery_app.conf.task_always_eager = False
    celery_app.conf.task_eager_propagates = False
    monkeypatch.delenv("USE_CELERY", raising=False)
    get_settings.cache_clear()


def test_create_novel_via_celery_eager(client, celery_eager):
    create_resp = client.post(
        "/api/novels",
        json={"premise": "Celery eager 小说", "genre": "xuanhuan", "target_chapters": 10},
    )
    assert create_resp.status_code == 201
    novel_id = create_resp.json()["id"]

    deadline = time.time() + 60.0
    while time.time() < deadline:
        body = client.get(f"/api/novels/{novel_id}").json()
        if body["status"] in ("planned", "failed"):
            break
        time.sleep(0.2)

    assert body["status"] == "planned", body.get("error")


def test_create_project_via_celery_eager(client, celery_eager):
    create_resp = client.post(
        "/api/projects",
        json={"story": "Celery eager 视频", "style": "vlog", "duration": 15, "aspect_ratio": "9:16"},
    )
    assert create_resp.status_code == 201
    project_id = create_resp.json()["id"]

    deadline = time.time() + 30.0
    while time.time() < deadline:
        body = client.get(f"/api/projects/{project_id}").json()
        if body["status"] in ("completed", "failed"):
            break
        time.sleep(0.2)

    assert body["status"] == "completed"


def _wait_novel_planned(client, novel_id: str, timeout: float = 60.0) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        body = client.get(f"/api/novels/{novel_id}").json()
        if body["status"] in ("planned", "failed"):
            break
        time.sleep(0.2)
    return client.get(f"/api/novels/{novel_id}").json()


def _wait_novel_done(client, novel_id: str, timeout: float = 60.0) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        body = client.get(f"/api/novels/{novel_id}").json()
        if body["status"] in ("completed", "failed", "review_required"):
            return body
        time.sleep(0.2)
    return client.get(f"/api/novels/{novel_id}").json()


def test_novel_start_writing_celery_eager(client, celery_eager):
    from app.tasks.novel_tasks import run_novel_start_writing_task

    create_resp = client.post(
        "/api/novels",
        json={"premise": "Celery start writing", "genre": "xuanhuan", "target_chapters": 10},
    )
    assert create_resp.status_code == 201
    novel_id = create_resp.json()["id"]
    assert _wait_novel_planned(client, novel_id)["status"] == "planned"

    result = run_novel_start_writing_task.delay(novel_id, 1)
    assert result.get()["status"] == "finished"

    body = _wait_novel_done(client, novel_id)
    assert body["status"] in ("completed", "review_required"), body.get("error")


def test_novel_next_chapter_celery_eager(client, celery_eager):
    from app.tasks.novel_tasks import run_novel_next_chapter_task, run_novel_start_writing_task

    create_resp = client.post(
        "/api/novels",
        json={"premise": "Celery next chapter", "genre": "dushi", "target_chapters": 10},
    )
    assert create_resp.status_code == 201
    novel_id = create_resp.json()["id"]
    assert _wait_novel_planned(client, novel_id)["status"] == "planned"

    run_novel_start_writing_task.delay(novel_id, 1)
    body = _wait_novel_done(client, novel_id)
    assert body["status"] in ("completed", "review_required"), body.get("error")

    result = run_novel_next_chapter_task.delay(novel_id, 1)
    assert result.get()["status"] == "finished"

    body = _wait_novel_done(client, novel_id)
    assert body["status"] in ("completed", "review_required"), body.get("error")
    indexes = sorted(c["index"] for c in body["chapters"])
    assert 2 in indexes
