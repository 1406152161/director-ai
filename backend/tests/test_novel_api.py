# @author zhangzhihao
"""小说 API 集成测试。"""

import time


def _wait_novel_done(client, novel_id: str, timeout: float = 30.0) -> dict:
    """等待生成结束（completed / failed / review_required）。"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        resp = client.get(f"/api/novels/{novel_id}")
        body = resp.json()
        if body["status"] in ("completed", "failed", "review_required"):
            return body
        time.sleep(0.2)
    return client.get(f"/api/novels/{novel_id}").json()


def _wait_novel_planned(client, novel_id: str, timeout: float = 30.0) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        resp = client.get(f"/api/novels/{novel_id}")
        body = resp.json()
        if body["status"] in ("completed", "failed", "planned"):
            return body
        time.sleep(0.2)
    return client.get(f"/api/novels/{novel_id}").json()


def test_create_novel_plan_then_write(client):
    create_resp = client.post(
        "/api/novels",
        json={"premise": "废柴少年逆袭成仙", "genre": "xuanhuan"},
    )
    assert create_resp.status_code == 201
    novel_id = create_resp.json()["id"]

    body = _wait_novel_planned(client, novel_id)
    assert body["status"] == "planned", body.get("error")

    start_resp = client.post(
        f"/api/novels/{novel_id}/start-writing",
        json={"write_count": 1},
    )
    assert start_resp.status_code == 200

    body = _wait_novel_done(client, novel_id)
    assert body["status"] == "completed", body.get("error")
    assert len(body["chapters"]) == 1
    ch = body["chapters"][0]
    assert ch["status"] == "completed"
    assert ch["content"]
    assert ch["word_count"] > 0


def test_continue_next_chapter(client):
    create_resp = client.post(
        "/api/novels",
        json={"premise": "都市白领逆袭", "genre": "dushi"},
    )
    novel_id = create_resp.json()["id"]
    body = _wait_novel_planned(client, novel_id)
    assert body["status"] == "planned"

    client.post(f"/api/novels/{novel_id}/start-writing", json={"write_count": 1})
    body = _wait_novel_done(client, novel_id)
    assert body["status"] == "completed"

    next_resp = client.post(
        f"/api/novels/{novel_id}/chapters/next",
        json={"write_count": 1},
    )
    assert next_resp.status_code == 200

    body = _wait_novel_done(client, novel_id)
    assert body["status"] == "completed"
    indexes = sorted(c["index"] for c in body["chapters"])
    assert 2 in indexes


def test_novel_chat(client):
    create_resp = client.post(
        "/api/novels",
        json={"premise": "甜宠恋爱故事", "genre": "tianai"},
    )
    novel_id = create_resp.json()["id"]
    body = _wait_novel_planned(client, novel_id)
    assert body["status"] == "planned"
    client.post(f"/api/novels/{novel_id}/start-writing", json={"write_count": 1})
    _wait_novel_done(client, novel_id)

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
    body = _wait_novel_planned(client, novel_id)
    assert body["status"] == "planned"
    client.post(f"/api/novels/{novel_id}/start-writing", json={"write_count": 1})
    _wait_novel_done(client, novel_id)

    md_resp = client.get(f"/api/novels/{novel_id}/export?format=md")
    assert md_resp.status_code == 200
    assert "attachment" in md_resp.headers.get("content-disposition", "")
    assert "#" in md_resp.text

    txt_resp = client.get(f"/api/novels/{novel_id}/export?format=txt")
    assert txt_resp.status_code == 200
    assert len(txt_resp.text) > 50


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


def test_plan_includes_full_bible_then_start_writing(client):
    create_resp = client.post(
        "/api/novels",
        json={
            "premise": "审大纲模式测试",
            "genre": "xuanhuan",
            "target_chapters": 10,
        },
    )
    assert create_resp.status_code == 201
    novel_id = create_resp.json()["id"]

    body = _wait_novel_planned(client, novel_id)
    assert body["status"] == "planned", body.get("error")
    bible = __import__("json").loads(body["bible_json"])
    assert len(bible["outline"]) >= 8
    assert bible.get("volumes")
    assert bible.get("foreshadowing")
    assert bible.get("items")

    start_resp = client.post(
        f"/api/novels/{novel_id}/start-writing",
        json={"write_count": 1},
    )
    assert start_resp.status_code == 200

    body = _wait_novel_done(client, novel_id)
    assert body["status"] == "completed", body.get("error")
    assert len(body["chapters"]) == 1


def test_patch_bible_world(client):
    create_resp = client.post(
        "/api/novels",
        json={"premise": "PATCH 测试", "genre": "kehuan"},
    )
    novel_id = create_resp.json()["id"]
    body = _wait_novel_planned(client, novel_id)
    assert body["status"] == "planned"

    patch_resp = client.patch(
        f"/api/novels/{novel_id}/bible",
        json={"world": "PATCH 后的世界观"},
    )
    assert patch_resp.status_code == 200
    bible = __import__("json").loads(patch_resp.json()["bible_json"])
    assert bible["world"] == "PATCH 后的世界观"


def test_novel_outline_pagination(client):
    create_resp = client.post(
        "/api/novels",
        json={
            "premise": "分页大纲测试",
            "genre": "xuanhuan",
            "target_chapters": 60,
        },
    )
    assert create_resp.status_code == 201
    novel_id = create_resp.json()["id"]
    body = _wait_novel_planned(client, novel_id, timeout=60.0)
    assert body["status"] == "planned", body.get("error")

    page1 = client.get(f"/api/novels/{novel_id}/outline?from=1&to=50")
    assert page1.status_code == 200
    assert len(page1.json()) == 50
    assert page1.json()[0]["index"] == 1
    assert page1.json()[49]["index"] == 50

    page2 = client.get(f"/api/novels/{novel_id}/outline?from=51&to=60")
    assert page2.status_code == 200
    assert len(page2.json()) == 10
    assert page2.json()[0]["index"] == 51


def test_rewrite_chapter_rejects_non_needs_review(client):
    create_resp = client.post(
        "/api/novels",
        json={"premise": "rewrite 409 测试", "genre": "xuanhuan", "target_chapters": 10},
    )
    novel_id = create_resp.json()["id"]
    body = _wait_novel_planned(client, novel_id)
    assert body["status"] == "planned"

    resp = client.post(f"/api/novels/{novel_id}/chapters/1/rewrite")
    assert resp.status_code == 409


def test_rewrite_chapter_after_needs_review(client, monkeypatch):
    _patch_validate_fail_twice(monkeypatch)

    create_resp = client.post(
        "/api/novels",
        json={"premise": "rewrite 流程测试", "genre": "xuanhuan", "target_chapters": 10},
    )
    novel_id = create_resp.json()["id"]
    body = _wait_novel_planned(client, novel_id)
    assert body["status"] == "planned"

    client.post(f"/api/novels/{novel_id}/start-writing", json={"write_count": 1})
    body = _wait_novel_done(client, novel_id, timeout=60.0)
    assert body["status"] == "review_required"
    assert body["chapters"][0]["status"] == "needs_review"

    rewrite_resp = client.post(f"/api/novels/{novel_id}/chapters/1/rewrite")
    assert rewrite_resp.status_code == 200

    body = _wait_novel_done(client, novel_id, timeout=60.0)
    assert body["status"] == "completed"
    assert body["chapters"][0]["status"] == "completed"


def _patch_validate_fail_twice(monkeypatch):
    """写章 + 自动重写各失败一次 → needs_review。"""
    from app.services.novel_validate_service import ValidationResult

    call_count = {"n": 0}

    async def fake_validate(self, *args, **kwargs):
        call_count["n"] += 1
        if call_count["n"] <= 2:
            return ValidationResult(passed=False, score=40, issues=["mock 校验问题"])
        return ValidationResult(passed=True, score=90, issues=[])

    monkeypatch.setattr(
        "app.services.novel_validate_service.NovelValidateService.validate_chapter",
        fake_validate,
    )


def test_approve_chapter_full_flow(client, monkeypatch):
    """T1：needs_review → 拦截续写 → approve → completed。"""
    _patch_validate_fail_twice(monkeypatch)

    create_resp = client.post(
        "/api/novels",
        json={"premise": "approve 流程测试", "genre": "xuanhuan", "target_chapters": 10},
    )
    novel_id = create_resp.json()["id"]
    assert _wait_novel_planned(client, novel_id)["status"] == "planned"

    client.post(f"/api/novels/{novel_id}/start-writing", json={"write_count": 1})
    body = _wait_novel_done(client, novel_id, timeout=60.0)
    assert body["status"] == "review_required"
    ch = body["chapters"][0]
    assert ch["status"] == "needs_review"
    assert ch["content"]

    blocked = client.post(
        f"/api/novels/{novel_id}/chapters/next",
        json={"write_count": 1},
    )
    assert blocked.status_code == 409

    bad_approve = client.post(f"/api/novels/{novel_id}/chapters/2/approve")
    assert bad_approve.status_code == 409

    approve_resp = client.post(f"/api/novels/{novel_id}/chapters/1/approve")
    assert approve_resp.status_code == 200

    body = _wait_novel_done(client, novel_id, timeout=60.0)
    assert body["status"] == "completed"
    ch = body["chapters"][0]
    assert ch["status"] == "completed"
    assert ch["validation_status"] == "passed"
    assert ch["word_count"] > 0

    next_resp = client.post(
        f"/api/novels/{novel_id}/chapters/next",
        json={"write_count": 1},
    )
    assert next_resp.status_code == 200


def test_chat_syncs_outline_to_db(client, monkeypatch):
    """T2：改稿对话返回 outline → sync 写入 novel_outline_items。"""
    create_resp = client.post(
        "/api/novels",
        json={"premise": "chat outline 测试", "genre": "xuanhuan", "target_chapters": 10},
    )
    novel_id = create_resp.json()["id"]
    assert _wait_novel_planned(client, novel_id)["status"] == "planned"

    before = client.get(f"/api/novels/{novel_id}/outline?from=5&to=5").json()
    assert len(before) == 1
    old_title = before[0]["title"]

    async def fake_chat(self, bible_json, message):
        from app.services.novel_memory_service import merge_bible_updates, parse_bible

        bible = parse_bible(bible_json)
        merged = merge_bible_updates(
            bible,
            {
                "outline": [
                    {
                        "index": 5,
                        "title": "Chat改后第五章",
                        "summary": "对话更新的摘要",
                        "hook": "对话更新的钩子",
                    }
                ]
            },
        )
        return "已更新第5章大纲", merged

    monkeypatch.setattr("app.services.novel_chat_service.NovelChatService.chat", fake_chat)

    chat_resp = client.post(
        f"/api/novels/{novel_id}/chat",
        json={"message": "把第5章标题改成更燃的"},
    )
    assert chat_resp.status_code == 200
    assert "第5章" in chat_resp.json()["reply"]

    row = client.get(f"/api/novels/{novel_id}/outline?from=5&to=5").json()
    assert len(row) == 1
    assert row[0]["title"] == "Chat改后第五章"
    assert row[0]["summary"] == "对话更新的摘要"
    assert row[0]["hook"] == "对话更新的钩子"
    assert row[0]["title"] != old_title

    bible = __import__("json").loads(chat_resp.json()["novel"]["bible_json"])
    assert bible.get("meta", {}).get("outline_in_db") is True
    assert bible.get("outline") == [] or len(bible.get("outline", [])) <= 500


def test_patch_bible_volumes_and_foreshadowing(client):
    create_resp = client.post(
        "/api/novels",
        json={"premise": "卷弧伏笔 PATCH", "genre": "xuanhuan", "target_chapters": 10},
    )
    novel_id = create_resp.json()["id"]
    body = _wait_novel_planned(client, novel_id)
    assert body["status"] == "planned"
    bible = __import__("json").loads(body["bible_json"])
    volumes = bible.get("volumes") or []
    foreshadowing = bible.get("foreshadowing") or []
    assert volumes
    assert foreshadowing

    volumes[0] = {**volumes[0], "title": "PATCH 后的卷名", "theme": "PATCH 主题"}
    foreshadowing[0] = {
        **foreshadowing[0],
        "content": "PATCH 后的伏笔内容",
        "plant_chapter": 2,
        "resolve_chapter": 9,
    }

    patch_resp = client.patch(
        f"/api/novels/{novel_id}/bible",
        json={"volumes": volumes, "foreshadowing": foreshadowing},
    )
    assert patch_resp.status_code == 200
    patched = __import__("json").loads(patch_resp.json()["bible_json"])
    assert patched["volumes"][0]["title"] == "PATCH 后的卷名"
    assert patched["foreshadowing"][0]["content"] == "PATCH 后的伏笔内容"
    assert patched["foreshadowing"][0]["resolve_chapter"] == 9


def test_written_chapter_has_beats_in_bible(client):
    create_resp = client.post(
        "/api/novels",
        json={"premise": "beat 展示测试", "genre": "xuanhuan", "target_chapters": 10},
    )
    novel_id = create_resp.json()["id"]
    assert _wait_novel_planned(client, novel_id)["status"] == "planned"
    client.post(f"/api/novels/{novel_id}/start-writing", json={"write_count": 1})
    body = _wait_novel_done(client, novel_id)
    assert body["status"] == "completed"
    bible = __import__("json").loads(body["bible_json"])
    beats = bible.get("beats") or {}
    assert beats.get("1") or beats.get(1)
    assert len(beats.get("1") or beats.get(1)) >= 1


def test_patch_foreshadowing_syncs_framework_items(client, db_session):
    create_resp = client.post(
        "/api/novels",
        json={"premise": "framework sync 测试", "genre": "xuanhuan", "target_chapters": 10},
    )
    novel_id = create_resp.json()["id"]
    body = _wait_novel_planned(client, novel_id)
    assert body["status"] == "planned"
    bible = __import__("json").loads(body["bible_json"])
    foreshadowing = list(bible.get("foreshadowing") or [])
    assert foreshadowing
    fs_id = foreshadowing[0]["id"]
    foreshadowing[0] = {
        **foreshadowing[0],
        "content": "Framework 同步的新伏笔",
        "resolve_chapter": 8,
    }

    patch_resp = client.patch(
        f"/api/novels/{novel_id}/bible",
        json={"foreshadowing": foreshadowing},
    )
    assert patch_resp.status_code == 200

    from app.models.novel_framework_item import NovelFrameworkItem
    from app.services.novel_framework_service import NovelFrameworkService

    row = (
        db_session.query(NovelFrameworkItem)
        .filter(
            NovelFrameworkItem.novel_id == novel_id,
            NovelFrameworkItem.item_type == "foreshadow",
            NovelFrameworkItem.item_key == fs_id,
        )
        .first()
    )
    assert row is not None
    assert row.content == "Framework 同步的新伏笔"
    assert row.chapter_to == 8

    svc = NovelFrameworkService(db_session)
    hits = svc.query_hybrid(novel_id, "Framework 同步的新伏笔", 8)
    assert hits
    assert any("Framework" in hit for hit in hits)


def test_retry_plan_resumes_after_failed(client, db_session):
    create_resp = client.post(
        "/api/novels",
        json={"premise": "retry plan 测试", "genre": "xuanhuan", "target_chapters": 10},
    )
    novel_id = create_resp.json()["id"]

    from app.models.novel import Novel

    novel = db_session.query(Novel).filter(Novel.id == novel_id).first()
    assert novel is not None
    novel.status = "failed"
    novel.error = "mock planning failure"
    db_session.commit()

    retry_resp = client.post(f"/api/novels/{novel_id}/retry-plan")
    assert retry_resp.status_code == 200
    assert retry_resp.json()["status"] in ("planning", "pending")

    planned = _wait_novel_planned(client, novel_id, timeout=60.0)
    assert planned["status"] == "planned"
    assert planned.get("error") in (None, "")


def test_retry_plan_rejects_when_already_planned(client):
    create_resp = client.post(
        "/api/novels",
        json={"premise": "retry 冲突测试", "genre": "xuanhuan", "target_chapters": 10},
    )
    novel_id = create_resp.json()["id"]
    assert _wait_novel_planned(client, novel_id)["status"] == "planned"

    conflict = client.post(f"/api/novels/{novel_id}/retry-plan")
    assert conflict.status_code == 409


def test_patch_items_syncs_framework_items(client, db_session):
    create_resp = client.post(
        "/api/novels",
        json={"premise": "道具 framework 测试", "genre": "xuanhuan", "target_chapters": 10},
    )
    novel_id = create_resp.json()["id"]
    body = _wait_novel_planned(client, novel_id)
    bible = __import__("json").loads(body["bible_json"])
    items = list(bible.get("items") or [])
    assert items
    item_id = items[0].get("id") or f"item_{items[0]['name']}"
    items[0] = {**items[0], "description": "PATCH 后的道具描述", "significance": "主线关键物"}

    patch_resp = client.patch(
        f"/api/novels/{novel_id}/bible",
        json={"items": items},
    )
    assert patch_resp.status_code == 200

    from app.models.novel_framework_item import NovelFrameworkItem

    row = (
        db_session.query(NovelFrameworkItem)
        .filter(
            NovelFrameworkItem.novel_id == novel_id,
            NovelFrameworkItem.item_type == "item",
            NovelFrameworkItem.item_key == item_id,
        )
        .first()
    )
    assert row is not None
    assert "PATCH 后的道具描述" in row.content


def test_delete_planned_novel(client, db_session):
    create_resp = client.post(
        "/api/novels",
        json={"premise": "删除测试", "genre": "xuanhuan", "target_chapters": 8},
    )
    novel_id = create_resp.json()["id"]
    assert _wait_novel_planned(client, novel_id)["status"] == "planned"

    resp = client.delete(f"/api/novels/{novel_id}")
    assert resp.status_code == 204
    assert client.get(f"/api/novels/{novel_id}").status_code == 404


def test_delete_planning_novel_conflict(client, db_session):
    from app.services.novel_service import NovelService

    create_resp = client.post(
        "/api/novels",
        json={"premise": "规划中不可删", "genre": "xuanhuan", "target_chapters": 8},
    )
    novel_id = create_resp.json()["id"]
    NovelService(db_session).update_status(novel_id, "planning")
    resp = client.delete(f"/api/novels/{novel_id}")
    assert resp.status_code == 409
