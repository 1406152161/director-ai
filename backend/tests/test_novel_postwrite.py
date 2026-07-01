# @author zhangzhihao
"""写后管线：条件 replan 集成测试。"""

import time

from app.core.config import get_settings
from app.providers.llm import mock as mock_llm


def _wait_planned(client, novel_id: str, timeout: float = 30.0) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        body = client.get(f"/api/novels/{novel_id}").json()
        if body["status"] == "planned":
            return body
        time.sleep(0.2)
    return client.get(f"/api/novels/{novel_id}").json()


def _wait_done(client, novel_id: str, timeout: float = 120.0) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        body = client.get(f"/api/novels/{novel_id}").json()
        if body["status"] in ("completed", "failed", "review_required"):
            return body
        time.sleep(0.2)
    return client.get(f"/api/novels/{novel_id}").json()


def _patch_replan_interval(monkeypatch, interval: int) -> None:
    monkeypatch.setenv("NOVEL_REPLAN_INTERVAL", str(interval))
    get_settings.cache_clear()


def _patch_replan_mock_total(monkeypatch, total: int) -> None:
    """mock replan 默认仅 8 章，需注入全书章数以便未写章可被调整。"""
    original = mock_llm._extract_total_chapters

    def _extract(text: str) -> int:
        if "已写至第" in text and "待调整 unwritten outline" in text:
            return total
        return original(text)

    monkeypatch.setattr("app.providers.llm.mock._extract_total_chapters", _extract)


def test_auto_replan_after_interval_updates_outline(client, monkeypatch):
    """写满 replan 间隔章后，postwrite 应自动 replan 未写章 outline。"""
    _patch_replan_interval(monkeypatch, 10)
    _patch_replan_mock_total(monkeypatch, 20)

    create_resp = client.post(
        "/api/novels",
        json={
            "premise": "postwrite auto replan 测试",
            "genre": "xuanhuan",
            "target_chapters": 20,
        },
    )
    assert create_resp.status_code == 201
    novel_id = create_resp.json()["id"]
    assert _wait_planned(client, novel_id)["status"] == "planned"

    before_ch11 = client.get(f"/api/novels/{novel_id}/outline?from=11&to=11").json()[0]
    assert "replan" not in before_ch11["title"]

    client.post(f"/api/novels/{novel_id}/start-writing", json={"write_count": 10})
    done = _wait_done(client, novel_id, timeout=180.0)
    assert done["status"] == "completed", done.get("error")
    assert done["progress"] >= 10

    deadline = time.time() + 30.0
    after_ch11 = before_ch11
    while time.time() < deadline:
        after_ch11 = client.get(f"/api/novels/{novel_id}/outline?from=11&to=11").json()[0]
        if "replan" in after_ch11["title"]:
            break
        time.sleep(0.2)

    assert "replan" in after_ch11["title"]
    assert after_ch11["title"] != before_ch11["title"]
    assert after_ch11["summary"].startswith("Replan 调整：")

    locked = client.get(f"/api/novels/{novel_id}/outline?from=1&to=10").json()
    assert all("replan" not in row["title"] for row in locked)
