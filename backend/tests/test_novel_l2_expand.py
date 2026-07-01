# @author zhangzhihao
"""M6 L2 滚动：l2_expand_range 与写作触发 L2 扩展。"""

import time

import pytest

from app.services.novel_plan_service import l2_expand_range


@pytest.mark.parametrize(
    ("last_written", "total", "expected"),
    [
        (0, 100, (1, 30)),
        (30, 100, (31, 60)),
        (60, 100, (61, 90)),
        (90, 100, (91, 100)),
        (100, 100, None),
        (95, 100, (96, 100)),
    ],
)
def test_l2_expand_range(last_written: int, total: int, expected):
    assert l2_expand_range(last_written, total) == expected


def _wait_planned(client, novel_id: str, timeout: float = 60.0) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        body = client.get(f"/api/novels/{novel_id}").json()
        if body["status"] == "planned":
            return body
        if body["status"] in ("failed", "review_required"):
            break
        time.sleep(0.2)
    return client.get(f"/api/novels/{novel_id}").json()


def test_plan_keeps_chapters_beyond_initial_l2_window_as_skeleton(client, monkeypatch):
    """规划阶段仅 L2 前 N 章；N+1 章仍为 skeleton。"""
    monkeypatch.setattr("app.services.novel_plan_service.L2_INITIAL_WINDOW", 5)

    create_resp = client.post(
        "/api/novels",
        json={
            "premise": "L2 规划窗口测试",
            "genre": "xuanhuan",
            "target_chapters": 12,
        },
    )
    assert create_resp.status_code == 201
    novel_id = create_resp.json()["id"]
    assert _wait_planned(client, novel_id)["status"] == "planned"

    ch3 = client.get(f"/api/novels/{novel_id}/outline?from=3&to=3").json()[0]
    ch8 = client.get(f"/api/novels/{novel_id}/outline?from=8&to=8").json()[0]
    assert ch3.get("detail_level") == "detailed"
    assert (ch3.get("hook") or "").strip()
    assert ch8.get("detail_level") == "skeleton"
    assert not (ch8.get("hook") or "").strip()
