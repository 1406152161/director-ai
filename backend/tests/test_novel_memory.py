# @author zhangzhihao
"""Chroma 记忆服务单元测试。"""

from app.services.novel_memory_service import NovelMemoryService


def test_chroma_add_and_query(tmp_path, monkeypatch):
    monkeypatch.setenv("CHROMA_PERSIST_DIR", str(tmp_path / "chroma"))
    from app.core.config import get_settings

    get_settings.cache_clear()

    svc = NovelMemoryService()
    svc.add_chapter_summary("novel-1", 1, "开篇", "主角踏上修行之路。")
    svc.add_chapter_summary("novel-1", 2, "奇遇", "主角获得神秘传承。")

    results = svc.query_relevant("novel-1", "传承", top_k=2)
    assert len(results) >= 1
