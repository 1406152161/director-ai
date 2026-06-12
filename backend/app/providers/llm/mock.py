# @author zhangzhihao
"""LLM Provider 占位实现。"""

import json

from app.core.config import Settings, get_settings
from app.providers.base import Message


class MockLLMProvider:
    """返回 mock 分镜脚本，供本地开发与测试。"""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    async def chat(self, messages: list[Message], **kwargs: object) -> str:
        user_content = messages[-1].content if messages else ""
        return json.dumps(
            {
                "title": "Mock 短片",
                "shots": [
                    {
                        "index": 1,
                        "scene_cn": f"画面：{user_content[:30]}",
                        "image_prompt_en": "cinematic wide shot, dramatic lighting",
                        "narration_cn": "开场旁白",
                        "duration": 4,
                    },
                    {
                        "index": 2,
                        "scene_cn": "特写镜头，情绪递进",
                        "image_prompt_en": "close-up shot, soft lighting, emotional",
                        "narration_cn": "第二镜旁白",
                        "duration": 4,
                    },
                ],
            },
            ensure_ascii=False,
        )
