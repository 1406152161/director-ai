# @author zhangzhihao
"""框架记忆 hybrid 检索单元测试。"""

import pytest

from app.services.novel_framework_service import NovelFrameworkService
from app.services.novel_memory_service import parse_bible


@pytest.fixture
def sample_bible():
    return parse_bible(
        '{"world":"测试世界","outline":[{"index":1,"title":"开篇","summary":"主角登场","hook":"悬念"}],'
        '"foreshadowing":[{"id":"fs1","content":"神秘玉佩","plant_chapter":1,"resolve_chapter":3,"status":"planned"}]}'
    )


def test_sync_and_query_hybrid(db_session, sample_bible):
    from app.models.novel import Novel

    novel = Novel(premise="测试", genre="xuanhuan", status="planned")
    db_session.add(novel)
    db_session.commit()

    svc = NovelFrameworkService(db_session)
    svc.sync_from_bible(novel.id, sample_bible)
    results = svc.query_hybrid(novel.id, "第1章 开篇", 1)
    assert results
    assert any("大纲" in r or "开篇" in r for r in results)


def test_sync_from_bible_idempotent(db_session, sample_bible):
    """重复 sync 相同 bible 不应膨胀行数。"""
    from app.models.novel import Novel
    from app.models.novel_framework_item import NovelFrameworkItem

    novel = Novel(premise="测试", genre="xuanhuan", status="planned")
    db_session.add(novel)
    db_session.commit()

    svc = NovelFrameworkService(db_session)
    svc.sync_from_bible(novel.id, sample_bible)
    count_first = (
        db_session.query(NovelFrameworkItem)
        .filter(NovelFrameworkItem.novel_id == novel.id)
        .count()
    )
    svc.sync_from_bible(novel.id, sample_bible)
    count_second = (
        db_session.query(NovelFrameworkItem)
        .filter(NovelFrameworkItem.novel_id == novel.id)
        .count()
    )
    assert count_first > 0
    assert count_second == count_first
