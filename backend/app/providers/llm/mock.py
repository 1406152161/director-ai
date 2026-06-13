# @author zhangzhihao
"""LLM Provider 占位实现。"""

import json
import re

from app.core.config import Settings, get_settings
from app.novel.prompts import (
    CHAT_MARKER,
    PLAN_MARKER,
    SUMMARY_MARKER,
    WRITE_MARKER,
)
from app.providers.base import Message

_MOCK_OUTLINE = [
    {"index": i, "title": f"第{i}章", "summary": f"第{i}章要点：主角继续冒险。"}
    for i in range(1, 9)
]

_MOCK_CHARACTERS = [
    {"name": "林凡", "role": "主角", "profile": "坚韧少年，偶得传承"},
    {"name": "苏婉", "role": "女主", "profile": "聪慧冷静，与主角并肩"},
]


def _messages_text(messages: list[Message]) -> str:
    return "\n".join(m.content for m in messages)


class MockLLMProvider:
    """返回 mock 分镜脚本或小说规划/章节，供本地开发与测试。"""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    async def chat(self, messages: list[Message], **kwargs: object) -> str:
        combined = _messages_text(messages)
        user_content = messages[-1].content if messages else ""

        if PLAN_MARKER in combined:
            return self._mock_novel_plan(user_content)
        if WRITE_MARKER in combined:
            return self._mock_chapter_content(user_content)
        if SUMMARY_MARKER in combined:
            return "本章主角遭遇危机后突破困境，与同伴关系更进一步，埋下后续伏笔。"
        if CHAT_MARKER in combined:
            return json.dumps(
                {
                    "reply": "已将女主性格调整得更主动，大纲相应微调。",
                    "updates": {
                        "characters": [
                            {
                                "name": "苏婉",
                                "role": "女主",
                                "traits": "主动果断，敢爱敢恨",
                            }
                        ],
                        "facts": ["女主在第三章主动提出结盟"],
                    },
                },
                ensure_ascii=False,
            )

        return self._mock_video_script(user_content)

    def _mock_novel_plan(self, premise: str) -> str:
        snippet = premise[:20] if premise else "未知创意"
        return json.dumps(
            {
                "title": f"Mock 小说：{snippet}",
                "synopsis": f"基于「{snippet}」展开的 mock 长篇故事。",
                "world": "架空大陆，灵气复苏，宗门林立。",
                "characters": _MOCK_CHARACTERS,
                "outline": _MOCK_OUTLINE,
            },
            ensure_ascii=False,
        )

    def _mock_chapter_content(self, prompt: str) -> str:
        chapter_match = re.search(r"第\s*(\d+)\s*章", prompt)
        chapter_num = chapter_match.group(1) if chapter_match else "1"
        paragraphs = [
            f"第{chapter_num}章开篇，风卷残云，主角立于山巅眺望远方。",
            "他回想起此前的种种经历，心中既有忐忑也有期待。",
            "同伴在身后轻声提醒，前路虽险，却不可退缩。",
            "二人踏入密林，异象频生，暗藏杀机。",
            "一番交锋后，主角悟得新法，实力再进一步。",
            "章节末尾，远处传来神秘钟声，新的旅程即将开启。",
        ]
        return "\n\n".join(paragraphs)

    def _mock_video_script(self, user_content: str) -> str:
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
