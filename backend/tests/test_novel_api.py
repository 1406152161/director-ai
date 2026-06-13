# @author zhangzhihao
"""小说 API 集成测试。"""

import time


def _wait_novel_completed(client, novel_id: str, timeout: float = 15.0) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        resp = client.get(f"/api/novels/{novel_id}")
        body = resp.json()
        if body["status"] in ("completed", "failed"):
            return body
        time.sleep(0.2)
    return client.get(f"/api/novels/{novel_id}").json()


def test_create_novel_and_generate_three_chapters(client):
    create_resp = client.post(
        "/api/novels",
        json={"premise": "废柴少年逆袭成仙", "genre": "xuanhuan"},
    )
    assert create_resp.status_code == 201
    novel_id = create_resp.json()["id"]

    body = _wait_novel_completed(client, novel_id)
    assert body["status"] == "completed", body.get("error")
    assert len(body["chapters"]) == 3
    for ch in body["chapters"]:
        assert ch["status"] == "completed"
        assert ch["content"]
        assert ch["word_count"] > 0


def test_continue_next_chapter(client):
    create_resp = client.post(
        "/api/novels",
        json={"premise": "都市白领逆袭", "genre": "dushi"},
    )
    novel_id = create_resp.json()["id"]
    _wait_novel_completed(client, novel_id)

    next_resp = client.post(f"/api/novels/{novel_id}/chapters/next")
    assert next_resp.status_code == 200

    body = _wait_novel_completed(client, novel_id)
    assert body["status"] == "completed"
    indexes = sorted(c["index"] for c in body["chapters"])
    assert 4 in indexes


def test_novel_chat(client):
    create_resp = client.post(
        "/api/novels",
        json={"premise": "甜宠恋爱故事", "genre": "tianai"},
    )
    novel_id = create_resp.json()["id"]
    _wait_novel_completed(client, novel_id)

    chat_resp = client.post(
        f"/api/novels/{novel_id}/chat",
        json={"message": "把女主改成更主动的性格"},
    )
    assert chat_resp.status_code == 200
    data = chat_resp.json()
    assert data["reply"]
    assert "主动" in data["novel"]["bible_json"]


def test_export_md_and_txt(client):
    create_resp = client.post(
        "/api/novels",
        json={"premise": "悬疑破案", "genre": "xuanyi"},
    )
    novel_id = create_resp.json()["id"]
    _wait_novel_completed(client, novel_id)

    md_resp = client.get(f"/api/novels/{novel_id}/export?format=md")
    assert md_resp.status_code == 200
    assert "attachment" in md_resp.headers.get("content-disposition", "")
    assert "#" in md_resp.text

    txt_resp = client.get(f"/api/novels/{novel_id}/export?format=txt")
    assert txt_resp.status_code == 200
    assert "第1章" in txt_resp.text or "第" in txt_resp.text


def test_list_novels(client):
    client.post("/api/novels", json={"premise": "科幻未来", "genre": "kehuan"})
    resp = client.get("/api/novels")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_create_invalid_genre(client):
    resp = client.post(
        "/api/novels",
        json={"premise": "测试", "genre": "invalid"},
    )
    assert resp.status_code == 400
