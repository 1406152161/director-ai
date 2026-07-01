# @author zhangzhihao
"""写后抽取上下文测试。"""

import json

from app.services.novel_extract_service import _bible_context_for_extract


def test_bible_context_preserves_core_and_summarizes_outline():
    outline = [{"index": i, "title": f"第{i}章"} for i in range(1, 61)]
    bible = {
        "world": "修仙世界",
        "power_system": "灵气体系",
        "characters": [{"name": "主角"}],
        "outline": outline,
    }
    context = _bible_context_for_extract(json.dumps(bible, ensure_ascii=False))
    assert "修仙世界" in context
    assert "灵气体系" in context
    assert '"characters"' in context
    assert "大纲摘要（前50章）" in context
    assert "第60章" not in context
