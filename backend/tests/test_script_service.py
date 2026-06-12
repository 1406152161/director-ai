# @author zhangzhihao
"""脚本生成服务测试。"""

import json

import pytest
from app.providers.base import Message
from app.services.script_service import ScriptService, _build_script_prompt


class MarkdownMockLLM:
    """模拟 LLM 返回 markdown 包裹的 JSON。"""

    def __init__(self) -> None:
        self.calls_kwargs: list[dict] = []

    async def chat(self, messages: list[Message], **kwargs: object) -> str:
        self.calls_kwargs.append(dict(kwargs))
        return (
            '好的，分镜如下：\n```json\n'
            + json.dumps(
                {
                    "title": "橘猫雨夜东京",
                    "shots": [
                        {
                            "index": 1,
                            "scene_cn": "雨夜霓虹街头",
                            "image_prompt_en": "orange cat in rainy tokyo street, neon lights",
                            "motion_prompt_en": "slow tracking shot, cat walks through rain",
                            "narration_cn": "雨夜，一只橘猫穿行东京。",
                            "duration": 4,
                        }
                    ],
                },
                ensure_ascii=False,
            )
            + "\n```"
        )


class RetryMockLLM:
    """第一次返回非法 JSON，第二次返回合法 JSON。"""

    def __init__(self) -> None:
        self.call_count = 0
        self.calls_kwargs: list[dict] = []

    async def chat(self, messages: list[Message], **kwargs: object) -> str:
        self.call_count += 1
        self.calls_kwargs.append(dict(kwargs))
        if self.call_count == 1:
            return "invalid json { broken"
        return json.dumps(
            {
                "title": "重试成功",
                "shots": [
                    {
                        "index": 1,
                        "scene_cn": "重试后镜头",
                        "image_prompt_en": "orange cat, cinematic",
                        "narration_cn": "重试旁白",
                        "duration": 4,
                    }
                ],
            },
            ensure_ascii=False,
        )


class AlwaysFailMockLLM:
    """始终返回无法解析的内容。"""

    def __init__(self) -> None:
        self.call_count = 0

    async def chat(self, messages: list[Message], **kwargs: object) -> str:
        self.call_count += 1
        return "not json at all"


def test_build_script_prompt_subject_constraints():
    prompt = _build_script_prompt("一个动漫版的橘猫走在东京街头", "cinematic", 15, 4)

    assert "主体保留" in prompt
    assert "motion_prompt_en" in prompt
    assert "禁止把动物拟人化或替换成人类" in prompt
    assert "核心主体稳定描述" in prompt
    assert "风格优先级" in prompt
    assert "仅当创意未明确风格时使用" in prompt


@pytest.mark.asyncio
async def test_generate_script_structured():
    svc = ScriptService()
    result = await svc.generate_script("橘猫雨夜东京", "cinematic", 15)

    assert result.title == "Mock 短片"
    assert len(result.shots) >= 1
    assert result.shots[0].scene_cn
    assert result.shots[0].image_prompt_en


@pytest.mark.asyncio
async def test_generate_script_markdown_tolerance():
    mock = MarkdownMockLLM()
    svc = ScriptService(llm=mock)
    result = await svc.generate_script("橘猫雨夜东京", "cinematic", 15)

    assert result.title == "橘猫雨夜东京"
    assert len(result.shots) == 1
    assert result.shots[0].scene_cn == "雨夜霓虹街头"
    assert "orange cat" in result.shots[0].image_prompt_en
    assert result.shots[0].motion_prompt_en
    for kwargs in mock.calls_kwargs:
        assert "enable_thinking" not in kwargs
        assert kwargs.get("max_tokens") == 8192


@pytest.mark.asyncio
async def test_generate_script_retries_on_parse_failure():
    mock = RetryMockLLM()
    svc = ScriptService(llm=mock)
    result = await svc.generate_script("橘猫雨夜东京", "cinematic", 15)

    assert mock.call_count == 2
    assert result.title == "重试成功"
    assert result.shots[0].scene_cn == "重试后镜头"
    for kwargs in mock.calls_kwargs:
        assert "enable_thinking" not in kwargs
        assert kwargs.get("max_tokens") == 8192


@pytest.mark.asyncio
async def test_generate_script_raises_after_retry_exhausted():
    mock = AlwaysFailMockLLM()
    svc = ScriptService(llm=mock)

    with pytest.raises(ValueError, match="未找到有效的 JSON"):
        await svc.generate_script("橘猫雨夜东京", "cinematic", 15)

    assert mock.call_count == 2
