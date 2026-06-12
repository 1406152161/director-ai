# @author zhangzhihao
"""脚本生成服务测试。"""

import json

import pytest
from app.providers.base import Message
from app.services.script_service import ScriptService, _build_script_prompt


class MarkdownMockLLM:
    """模拟 LLM 返回 markdown 包裹的 JSON。"""

    async def chat(self, messages: list[Message], **kwargs: object) -> str:
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
                            "narration_cn": "雨夜，一只橘猫穿行东京。",
                            "duration": 4,
                        }
                    ],
                },
                ensure_ascii=False,
            )
            + "\n```"
        )


def test_build_script_prompt_subject_constraints():
    prompt = _build_script_prompt("一个动漫版的橘猫走在东京街头", "cinematic", 15, 4)

    assert "主体保留" in prompt
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
    svc = ScriptService(llm=MarkdownMockLLM())
    result = await svc.generate_script("橘猫雨夜东京", "cinematic", 15)

    assert result.title == "橘猫雨夜东京"
    assert len(result.shots) == 1
    assert result.shots[0].scene_cn == "雨夜霓虹街头"
    assert "orange cat" in result.shots[0].image_prompt_en
