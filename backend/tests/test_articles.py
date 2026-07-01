# @author zhangzhihao
"""图文 API 测试。"""


def test_create_and_get_article(client):
    create = client.post(
        "/api/articles",
        json={
            "topic": "春季露营装备清单",
            "platform": "xiaohongshu",
            "tone": "friendly",
        },
    )
    assert create.status_code == 201
    body = create.json()
    assert body["status"] == "preview"
    assert "春季露营" in body["title"]
    assert body["body_md"]

    get_resp = client.get(f"/api/articles/{body['id']}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == body["id"]


def test_list_and_delete_article(client):
    client.post(
        "/api/articles",
        json={"topic": "待删图文", "platform": "general", "tone": "formal"},
    )
    listed = client.get("/api/articles").json()
    assert len(listed) >= 1
    article_id = listed[0]["id"]

    del_resp = client.delete(f"/api/articles/{article_id}")
    assert del_resp.status_code == 204
    assert client.get(f"/api/articles/{article_id}").status_code == 404
