# @author zhangzhihao
"""项目 API 测试。"""

import time


def test_create_and_get_project(client):
    create_resp = client.post(
        "/api/projects",
        json={
            "story": "测试创意描述",
            "style": "vlog",
            "duration": 30,
            "aspect_ratio": "9:16",
        },
    )
    assert create_resp.status_code == 201
    body = create_resp.json()
    assert body["id"]
    assert body["story"] == "测试创意描述"
    assert body["status"] == "pending"
    assert body["aspect_ratio"] == "9:16"

    get_resp = client.get(f"/api/projects/{body['id']}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == body["id"]


def test_get_project_not_found(client):
    resp = client.get("/api/projects/non-existent-id")
    assert resp.status_code == 404


def test_list_projects(client):
    client.post(
        "/api/projects",
        json={"story": "作品A", "style": "cinematic", "duration": 15, "aspect_ratio": "9:16"},
    )
    client.post(
        "/api/projects",
        json={"story": "作品B", "style": "anime", "duration": 30, "aspect_ratio": "1:1"},
    )

    # 等待后台任务不影响列表查询
    time.sleep(0.2)

    resp = client.get("/api/projects")
    assert resp.status_code == 200
    projects = resp.json()
    assert len(projects) >= 2
    stories = {p["story"] for p in projects}
    assert "作品A" in stories
    assert "作品B" in stories


def test_retry_failed_project(client, db_session):
    from app.schemas.project import ProjectCreate
    from app.services.project_service import ProjectService

    svc = ProjectService(db_session)
    project = svc.create_project(
        ProjectCreate(
            story="retry 失败项目测试",
            style="vlog",
            duration=15,
            aspect_ratio="9:16",
        )
    )
    project_id = project.id
    svc.set_failed(project_id, "mock generation failure")

    retry_resp = client.post(f"/api/projects/{project_id}/retry")
    assert retry_resp.status_code == 200
    assert retry_resp.json()["status"] == "pending"
    assert retry_resp.json()["error"] in (None, "")

    deadline = time.time() + 30.0
    while time.time() < deadline:
        body = client.get(f"/api/projects/{project_id}").json()
        if body["status"] in ("completed", "failed"):
            break
        time.sleep(0.2)

    assert body["status"] == "completed", body.get("error")


def test_delete_completed_project(client, db_session):
    from app.schemas.project import ProjectCreate
    from app.services.project_service import ProjectService

    svc = ProjectService(db_session)
    project = svc.create_project(
        ProjectCreate(story="待删项目", style="vlog", duration=15, aspect_ratio="9:16")
    )
    project_id = project.id
    svc.update_status(project_id, "completed", progress=100)

    resp = client.delete(f"/api/projects/{project_id}")
    assert resp.status_code == 204
    assert client.get(f"/api/projects/{project_id}").status_code == 404


def test_delete_active_project_conflict(client, db_session):
    from app.schemas.project import ProjectCreate
    from app.services.project_service import ProjectService

    svc = ProjectService(db_session)
    project = svc.create_project(
        ProjectCreate(story="进行中", style="vlog", duration=15, aspect_ratio="9:16")
    )
    resp = client.delete(f"/api/projects/{project.id}")
    assert resp.status_code == 409
