# @author zhangzhihao
"""章节质量校验单元测试。"""

import pytest
from app.services.novel_validate_service import PASS_SCORE, NovelValidateService


@pytest.mark.asyncio
async def test_validate_chapter_mock_passes():
    svc = NovelValidateService()
    outline = {"index": 1, "title": "开篇", "summary": "主角登场", "hook": "悬念"}
    beats = [{"index": 1, "scene": "山巅", "goal": "铺垫", "conflict": "危机", "outcome": "下山"}]
    content = "这是一段足够长的测试正文。" * 10
    result = await svc.validate_chapter(
        genre="xuanhuan",
        chapter_index=1,
        title="开篇",
        content=content,
        summary="测试摘要",
        word_count=len(content),
        outline=outline,
        beats=beats,
        foreshadowing=[],
        bible_summary="世界观测试",
    )
    assert result.passed
    assert result.score >= PASS_SCORE


def test_validate_rules_empty_content():
    svc = NovelValidateService()
    issues = svc.validate_rules("", 0, {"summary": "x"})
    assert any("过短" in i or "为空" in i for i in issues)
