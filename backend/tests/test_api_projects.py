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
