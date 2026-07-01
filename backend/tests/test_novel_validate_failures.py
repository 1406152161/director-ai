# @author zhangzhihao
"""校验失败 → needs_review / review_required 集成测试。"""

import time

from app.services.novel_validate_service import ValidationResult


def _wait_planned(client, novel_id: str, timeout: float = 30.0) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        body = client.get(f"/api/novels/{novel_id}").json()
        if body["status"] == "planned":
            return body
        time.sleep(0.2)
    return client.get(f"/api/novels/{novel_id}").json()


def _wait_done(client, novel_id: str, timeout: float = 60.0) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        body = client.get(f"/api/novels/{novel_id}").json()
        if body["status"] in ("completed", "failed", "review_required"):
            return body
        time.sleep(0.2)
    return client.get(f"/api/novels/{novel_id}").json()


def _patch_validate_always_fail(monkeypatch) -> None:
    async def fake_validate(self, *args, **kwargs):
        return ValidationResult(passed=False, score=40, issues=["mock 校验未通过"])

    monkeypatch.setattr(
        "app.services.novel_validate_service.NovelValidateService.validate_chapter",
        fake_validate,
    )


def test_validate_failure_sets_needs_review_and_review_required(client, monkeypatch):
    _patch_validate_always_fail(monkeypatch)

    create_resp = client.post(
        "/api/novels",
        json={
            "premise": "校验失败测试",
            "genre": "xuanhuan",
            "target_chapters": 10,
        },
    )
    assert create_resp.status_code == 201
    novel_id = create_resp.json()["id"]
    assert _wait_planned(client, novel_id)["status"] == "planned"

    client.post(f"/api/novels/{novel_id}/start-writing", json={"write_count": 1})
    body = _wait_done(client, novel_id)
    assert body["status"] == "review_required"
    assert len(body["chapters"]) == 1

    ch = body["chapters"][0]
    assert ch["status"] == "needs_review"
    assert ch["validation_status"] == "needs_review"
    assert ch["content"]
    assert ch["validation_score"] == 40
