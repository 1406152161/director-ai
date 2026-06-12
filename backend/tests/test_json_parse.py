# @author zhangzhihao
"""JSON 容错解析单元测试。"""

import pytest
from app.utils.json_parse import parse_json_from_llm


def test_parse_plain_json():
    text = '{"title": "测试", "shots": []}'
    result = parse_json_from_llm(text)
    assert result["title"] == "测试"


def test_parse_markdown_fence():
    text = """这是前言
```json
{"title": "短片", "shots": [{"index": 1}]}
```
后续噪声"""
    result = parse_json_from_llm(text)
    assert result["title"] == "短片"
    assert result["shots"][0]["index"] == 1


def test_parse_with_noise():
    text = '好的，以下是分镜：\n{"title": "橘猫", "shots": []}\n希望满意！'
    result = parse_json_from_llm(text)
    assert result["title"] == "橘猫"


def test_parse_invalid_raises():
    with pytest.raises(ValueError, match="未找到有效的 JSON"):
        parse_json_from_llm("没有 json 内容")
