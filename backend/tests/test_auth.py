# @author zhangzhihao
"""鉴权 API 测试。"""

import pytest


@pytest.fixture
def auth_client(client, monkeypatch):
    monkeypatch.setenv("AUTH_ENABLED", "true")
    monkeypatch.setenv("JWT_SECRET", "test-secret-key")
    get_settings = __import__("app.core.config", fromlist=["get_settings"]).get_settings
    get_settings.cache_clear()
    yield client
    get_settings.cache_clear()


def test_auth_disabled_by_default(client):
    resp = client.get("/api/auth/status")
    assert resp.status_code == 200
    assert resp.json()["enabled"] is False


def test_register_and_login(auth_client):
    reg = auth_client.post(
        "/api/auth/register",
        json={
            "email": "dev@example.com",
            "password": "secret12",
            "display_name": "测试用户",
        },
    )
    assert reg.status_code == 201
    token = reg.json()["access_token"]
    assert token

    me = auth_client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "dev@example.com"

    login = auth_client.post(
        "/api/auth/login",
        json={"email": "dev@example.com", "password": "secret12"},
    )
    assert login.status_code == 200
    assert login.json()["access_token"]


def test_project_scoped_when_auth_enabled(auth_client):
    reg = auth_client.post(
        "/api/auth/register",
        json={"email": "owner@example.com", "password": "secret12"},
    )
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    create = auth_client.post(
        "/api/auth/register",
        json={"email": "other@example.com", "password": "secret12"},
    )
    other_token = create.json()["access_token"]

    proj = auth_client.post(
        "/api/projects",
        json={"story": "私有项目", "style": "vlog", "duration": 15, "aspect_ratio": "9:16"},
        headers=headers,
    )
    assert proj.status_code == 201
    project_id = proj.json()["id"]

    listed = auth_client.get("/api/projects", headers=headers).json()
    assert any(p["id"] == project_id for p in listed)

    other_list = auth_client.get(
        "/api/projects",
        headers={"Authorization": f"Bearer {other_token}"},
    ).json()
    assert not any(p["id"] == project_id for p in other_list)
