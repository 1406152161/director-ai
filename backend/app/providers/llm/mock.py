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
                "assets": {
                    "characters": [
                        {
                            "id": "char_main",
                            "name_cn": "主角",
                            "description_en": (
                                "an orange tabby cat, anime style, consistent appearance"
                            ),
                        }
                    ],
                    "scenes": [
                        {
                            "id": "scene_main",
                            "name_cn": "主场景",
                            "description_en": (
                                "Tokyo street at dusk, neon signs, anime background"
                            ),
                        }
                    ],
                    "props": [],
                },
                "shots": [
                    {
                        "index": 1,
                        "character_ids": ["char_main"],
                        "scene_id": "scene_main",
                        "prop_ids": [],
                        "scene_cn": f"画面：{user_content[:30]}",
                        "image_prompt_en": (
                            "anime style, orange tabby cat, cinematic wide shot, "
                            "dramatic lighting"
                        ),
                        "motion_prompt_en": (
                            "slow pan, gentle camera movement, subject walks forward"
                        ),
                        "narration_cn": "开场旁白",
                        "duration": 4,
                    },
                    {
                        "index": 2,
                        "character_ids": ["char_main"],
                        "scene_id": "scene_main",
                        "prop_ids": [],
                        "scene_cn": "特写镜头，情绪递进",
                        "image_prompt_en": (
                            "anime style, orange tabby cat, close-up shot, "
                            "soft lighting, emotional"
                        ),
                        "motion_prompt_en": (
                            "slow zoom in, subtle subject movement, cinematic"
                        ),
                        "narration_cn": "第二镜旁白",
                        "duration": 4,
                    },
                ],
            },
            ensure_ascii=False,
        )
