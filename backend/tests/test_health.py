# @author zhangzhihao
"""API 健康检查测试。"""

import pytest
from app.main import app
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_health_returns_ok():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "director-ai"


def test_health_deep_returns_checks(client):
    resp = client.get("/api/health?deep=true")
    assert resp.status_code == 200
    data = resp.json()
    assert data["service"] == "director-ai"
    assert "checks" in data
    assert data["checks"]["database"] == "ok"
    assert "redis" in data["checks"]
