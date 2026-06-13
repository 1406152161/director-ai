# @author zhangzhihao
"""小说工具与 Story Bible 单元测试。"""

import json

from app.novel.utils import count_chinese_words
from app.services.novel_memory_service import merge_bible_updates, parse_bible


def test_count_chinese_words():
    text = "你好 世界\n测试"
    assert count_chinese_words(text) == 6


def test_parse_bible_empty():
    bible = parse_bible("")
    assert bible["facts"] == []
    assert bible["outline"] == []


def test_merge_bible_updates_characters_and_facts():
    bible = {
        "world": "原世界观",
        "facts": ["事实A"],
        "characters": [{"name": "苏婉", "role": "女主", "traits": "温柔"}],
        "outline": [{"index": 1, "title": "开篇", "summary": "起"}],
    }
    updates = {
        "world": "新世界观",
        "characters": [{"name": "苏婉", "traits": "主动果断"}],
        "facts": ["事实B"],
    }
    merged = merge_bible_updates(bible, updates)
    assert merged["world"] == "新世界观"
    assert merged["characters"][0]["traits"] == "主动果断"
    assert "事实B" in merged["facts"]
    assert "事实A" in merged["facts"]
