# @author zhangzhihao
"""outline DB SSOT：chat / replan / sync 集成测试。"""

import json
import time


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


def test_patch_bible_syncs_outline_to_db(client):
    create_resp = client.post(
        "/api/novels",
        json={"premise": "outline sync 测试", "genre": "xuanhuan", "target_chapters": 10},
    )
    novel_id = create_resp.json()["id"]
    assert _wait_planned(client, novel_id)["status"] == "planned"

    patch_resp = client.patch(
        f"/api/novels/{novel_id}/bible",
        json={
            "outline": [
                {
                    "index": 3,
                    "title": "PATCH 第三章",
                    "summary": "摘要更新",
                    "hook": "新钩子",
                }
            ]
        },
    )
    assert patch_resp.status_code == 200

    row = client.get(f"/api/novels/{novel_id}/outline?from=3&to=3").json()
    assert len(row) == 1
    assert row[0]["title"] == "PATCH 第三章"
    assert row[0]["hook"] == "新钩子"

    bible = json.loads(patch_resp.json()["bible_json"])
    assert bible.get("outline") == [] or len(bible.get("outline", [])) <= 500
    assert bible.get("meta", {}).get("outline_in_db") is True


def test_replan_after_writing_keeps_outline_in_db(client):
    create_resp = client.post(
        "/api/novels",
        json={"premise": "replan db 测试", "genre": "xuanhuan", "target_chapters": 10},
    )
    novel_id = create_resp.json()["id"]
    assert _wait_planned(client, novel_id)["status"] == "planned"

    before = client.get(f"/api/novels/{novel_id}/outline?from=4&to=10").json()
    assert len(before) == 7

    client.post(f"/api/novels/{novel_id}/start-writing", json={"write_count": 1})
    assert _wait_done(client, novel_id)["status"] == "completed"

    replan_resp = client.post(f"/api/novels/{novel_id}/replan")
    assert replan_resp.status_code == 200

    after = client.get(f"/api/novels/{novel_id}/outline?from=1&to=10").json()
    assert len(after) == 10
    assert after[0]["index"] == 1
    assert after[9]["index"] == 10


def test_chat_syncs_indexes_and_outline_api(client):
    create_resp = client.post(
        "/api/novels",
        json={"premise": "chat sync 测试", "genre": "tianai", "target_chapters": 10},
    )
    novel_id = create_resp.json()["id"]
    assert _wait_planned(client, novel_id)["status"] == "planned"

    client.post(f"/api/novels/{novel_id}/start-writing", json={"write_count": 1})
    assert _wait_done(client, novel_id)["status"] == "completed"

    chat_resp = client.post(
        f"/api/novels/{novel_id}/chat",
        json={"message": "把女主改成更主动"},
    )
    assert chat_resp.status_code == 200
    bible = json.loads(chat_resp.json()["novel"]["bible_json"])
    assert bible.get("meta", {}).get("outline_in_db") is True
    assert "主动" in chat_resp.json()["novel"]["bible_json"]

    outline_resp = client.get(f"/api/novels/{novel_id}/outline?from=1&to=10")
    assert len(outline_resp.json()) == 10


def test_replan_updates_outline_from_chapter_four(client):
    """写 3 章后手动 replan，第 4 章及以后 outline 应被 mock 调整。"""
    create_resp = client.post(
        "/api/novels",
        json={"premise": "replan 未写章测试", "genre": "xuanhuan", "target_chapters": 10},
    )
    novel_id = create_resp.json()["id"]
    assert _wait_planned(client, novel_id)["status"] == "planned"

    before_ch4 = client.get(f"/api/novels/{novel_id}/outline?from=4&to=4").json()[0]
    assert "replan" not in before_ch4["title"]

    client.post(f"/api/novels/{novel_id}/start-writing", json={"write_count": 3})
    done = _wait_done(client, novel_id, timeout=90.0)
    assert done["status"] == "completed"
    assert done["progress"] >= 3

    replan_resp = client.post(f"/api/novels/{novel_id}/replan")
    assert replan_resp.status_code == 200

    deadline = time.time() + 30.0
    after_ch4 = before_ch4
    while time.time() < deadline:
        after_ch4 = client.get(f"/api/novels/{novel_id}/outline?from=4&to=4").json()[0]
        if "replan" in after_ch4["title"]:
            break
        time.sleep(0.2)

    assert "replan" in after_ch4["title"]
    assert after_ch4["title"] != before_ch4["title"]
    assert after_ch4["summary"].startswith("Replan 调整：")

    locked = client.get(f"/api/novels/{novel_id}/outline?from=1&to=3").json()
    assert all("replan" not in row["title"] for row in locked)
