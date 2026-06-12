# @author zhangzhihao
"""端到端冒烟测试 — 需真实 Agnes API Key，CI 默认跳过。

手动运行：
  cd backend
  set AGNES_API_KEY=sk-xxx  (PowerShell: $env:AGNES_API_KEY="sk-xxx")
  set LLM_PROVIDER=agnes
  set IMAGE_PROVIDER=agnes
  pytest -m e2e -v
"""

import os
import time

import pytest
from app.main import app
from fastapi.testclient import TestClient

pytestmark = pytest.mark.e2e


@pytest.fixture
def e2e_client():
    if not os.environ.get("AGNES_API_KEY"):
        pytest.skip("未设置 AGNES_API_KEY，跳过 e2e 测试")
    with TestClient(app) as client:
        yield client


def test_e2e_orange_cat_tokyo(e2e_client):
    """真实 Key 跑「橘猫雨夜东京」→ 出脚本 + 可访问竖屏图。"""
    resp = e2e_client.post(
        "/api/projects",
        json={
            "story": "一只橘猫在雨夜穿越霓虹灯下的东京街头",
            "style": "cinematic",
            "duration": 15,
            "aspect_ratio": "9:16",
        },
    )
    assert resp.status_code == 201
    project_id = resp.json()["id"]

    data = None
    for _ in range(120):
        detail = e2e_client.get(f"/api/projects/{project_id}")
        data = detail.json()
        if data["status"] in ("completed", "failed"):
            break
        time.sleep(2)

    assert data is not None
    assert data["status"] == "completed", f"生成失败: {data.get('error')}"
    assert data["title"]
    assert len(data["shots"]) >= 1
    for shot in data["shots"]:
        assert shot["image_url"]
        assert shot["scene_cn"]
        assert shot["narration_cn"]
