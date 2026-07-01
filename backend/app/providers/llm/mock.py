# @author zhangzhihao
"""LLM Provider 占位实现。"""

import json
import re

from app.core.config import Settings, get_settings
from app.novel.prompts import (
    BEAT_MARKER,
    CHAT_MARKER,
    EXTRACT_MARKER,
    PLAN_OUTLINE_DETAIL_MARKER,
    PLAN_OUTLINE_MARKER,
    PLAN_OUTLINE_SKELETON_MARKER,
    PLAN_WORLD_MARKER,
    REPLAN_MARKER,
    ROLLING_SUMMARY_MARKER,
    SUMMARY_MARKER,
    VALIDATE_MARKER,
    WRITE_MARKER,
)
from app.providers.base import Message

_MOCK_CHARACTERS = [
    {
        "name": "林凡",
        "role": "主角",
        "profile": "坚韧少年，偶得传承",
        "growth_arc": "废柴→觉醒→宗门新星",
    },
    {
        "name": "苏婉",
        "role": "女主",
        "profile": "聪慧冷静，与主角并肩",
        "growth_arc": "旁观者→盟友→心意相通",
    },
]

_MOCK_VOLUMES = [
    {
        "id": "v1",
        "title": "初入修行",
        "theme": "觉醒与入门",
        "chapter_from": 1,
        "chapter_to": 8,
        "arcs": [
            {
                "id": "v1a1",
                "title": "机缘",
                "conflict": "废柴身份与秘境机缘",
                "chapter_from": 1,
                "chapter_to": 4,
            },
            {
                "id": "v1a2",
                "title": "宗门试炼",
                "conflict": "外门打压与实力证明",
                "chapter_from": 5,
                "chapter_to": 8,
            },
        ],
    },
]

_MOCK_FORESHADOWING = [
    {
        "id": "fs1",
        "content": "古玉中的神秘符文",
        "plant_chapter": 2,
        "resolve_chapter": 7,
        "status": "planned",
        "linked_characters": ["林凡"],
        "linked_items": ["古玉"],
        "linked_beats": [],
    },
    {
        "id": "fs2",
        "content": "苏婉身世的暗示",
        "plant_chapter": 3,
        "resolve_chapter": 8,
        "status": "planned",
        "linked_characters": ["苏婉"],
        "linked_items": [],
        "linked_beats": [],
    },
]


def _messages_text(messages: list[Message]) -> str:
    return "\n".join(m.content for m in messages)


def _extract_total_chapters(text: str) -> int:
    match = re.search(r"用户目标\s*(\d+)\s*章", text)
    if match:
        return max(8, min(10000, int(match.group(1))))
    match = re.search(r"全书共\s*(\d+)\s*章", text)
    if match:
        return max(8, min(10000, int(match.group(1))))
    match = re.search(r"共\s*(\d+)\s*章", text)
    if match:
        return max(8, min(10000, int(match.group(1))))
    match = re.search(r"目标章数：\s*(\d+)", text)
    if match:
        return max(8, min(10000, int(match.group(1))))
    return 8


def _extract_outline_range(text: str) -> tuple[int, int] | None:
    match = re.search(r"第\s*(\d+)\s*[–\-]\s*(\d+)\s*章", text)
    if match:
        return int(match.group(1)), int(match.group(2))
    return None


def _mock_outline_for_range(start: int, end: int, *, with_hook: bool = False) -> list[dict]:
    items = []
    span = end - start + 1
    for i in range(start, end + 1):
        arc_id = "v1a1" if i <= start + span // 2 else "v1a2"
        item = {
            "index": i,
            "title": f"第{i}章",
            "summary": f"第{i}章要点：主角继续冒险，推进主线。",
            "arc_id": arc_id,
            "volume_id": "v1",
        }
        if with_hook:
            item["hook"] = f"章末悬念 {i}"
        items.append(item)
    return items


def _mock_outline(total: int) -> list[dict]:
    return _mock_outline_for_range(1, total)


class MockLLMProvider:
    """返回 mock 分镜脚本或小说规划/章节，供本地开发与测试。"""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    async def chat(self, messages: list[Message], **kwargs: object) -> str:
        combined = _messages_text(messages)
        user_content = messages[-1].content if messages else ""

        if PLAN_WORLD_MARKER in combined:
            return self._mock_plan_world(user_content)
        if PLAN_OUTLINE_SKELETON_MARKER in combined:
            return self._mock_plan_skeleton(user_content)
        if PLAN_OUTLINE_DETAIL_MARKER in combined:
            return self._mock_plan_detail(user_content)
        if PLAN_OUTLINE_MARKER in combined:
            return self._mock_plan_outline(user_content)
        if BEAT_MARKER in combined:
            return self._mock_beats(user_content)
        if VALIDATE_MARKER in combined:
            return self._mock_validate(user_content)
        if EXTRACT_MARKER in combined:
            return self._mock_extract()
        if ROLLING_SUMMARY_MARKER in combined:
            return self._mock_rolling_summary(user_content)
        if REPLAN_MARKER in combined:
            return self._mock_replan(user_content)
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

    def _mock_plan_world(self, premise: str) -> str:
        snippet = premise[:20] if premise else "未知创意"
        total = _extract_total_chapters(premise)
        return json.dumps(
            {
                "title": f"Mock 小说：{snippet}",
                "synopsis": f"基于「{snippet}」展开的 mock 长篇故事。",
                "world": "架空大陆，灵气复苏，宗门林立。",
                "power_system": "炼气→筑基→金丹；灵石为修行资源。",
                "items": [
                    {
                        "id": "item1",
                        "name": "古玉",
                        "description": "上古传承载体",
                        "significance": "贯穿主线",
                        "first_chapter": 1,
                    }
                ],
                "characters": _MOCK_CHARACTERS,
                "volumes": _MOCK_VOLUMES,
                "foreshadowing": _MOCK_FORESHADOWING,
                "meta": {"total_chapters": total},
            },
            ensure_ascii=False,
        )

    def _mock_plan_skeleton(self, user_content: str) -> str:
        rng = _extract_outline_range(user_content)
        if rng:
            start, end = rng
            return json.dumps(
                {"outline": _mock_outline_for_range(start, end, with_hook=False)},
                ensure_ascii=False,
            )
        total = _extract_total_chapters(user_content)
        return json.dumps(
            {"outline": _mock_outline_for_range(1, total, with_hook=False)},
            ensure_ascii=False,
        )

    def _mock_plan_detail(self, user_content: str) -> str:
        rng = _extract_outline_range(user_content)
        if rng:
            start, end = rng
            return json.dumps(
                {"outline": _mock_outline_for_range(start, end, with_hook=True)},
                ensure_ascii=False,
            )
        total = min(_extract_total_chapters(user_content), 60)
        return json.dumps(
            {"outline": _mock_outline_for_range(1, total, with_hook=True)},
            ensure_ascii=False,
        )

    def _mock_plan_outline(self, user_content: str) -> str:
        rng = _extract_outline_range(user_content)
        if rng:
            start, end = rng
            return json.dumps(
                {"outline": _mock_outline_for_range(start, end, with_hook=True)},
                ensure_ascii=False,
            )
        total = _extract_total_chapters(user_content)
        return json.dumps({"outline": _mock_outline(total)}, ensure_ascii=False)

    def _mock_extract(self) -> str:
        return json.dumps(
            {
                "facts": ["mock 新事实：主角与同伴关系加深"],
                "entity_updates": [
                    {
                        "entity_key": "char_林凡",
                        "entity_type": "character",
                        "name": "林凡",
                        "updates": {"location": "密林"},
                    }
                ],
                "foreshadowing_updates": [],
            },
            ensure_ascii=False,
        )

    def _mock_rolling_summary(self, user_content: str) -> str:
        return json.dumps(
            {
                "book": "mock 全书：少年修行成长线。",
                "volume": "mock 当前卷：初入宗门。",
                "arc": "mock 当前弧：秘境与试炼。",
            },
            ensure_ascii=False,
        )

    def _mock_replan(self, user_content: str) -> str:
        total = _extract_total_chapters(user_content)
        outline = _mock_outline(total)
        last_written = 0
        match = re.search(r"已写至第\s*(\d+)\s*章", user_content)
        if match:
            last_written = int(match.group(1))
        for item in outline:
            idx = int(item.get("index", 0))
            if idx > last_written:
                item["title"] = f"{item['title']} replan"
                item["summary"] = f"Replan 调整：{item['summary']}"
        return json.dumps(
            {
                "outline": outline,
                "foreshadowing": _MOCK_FORESHADOWING,
            },
            ensure_ascii=False,
        )

    def _mock_validate(self, user_content: str) -> str:
        return json.dumps(
            {
                "passed": True,
                "score": 85,
                "issues": [],
                "checks": {
                    "beat_coverage": True,
                    "foreshadowing": True,
                    "outline_alignment": True,
                    "consistency": True,
                },
            },
            ensure_ascii=False,
        )

    def _mock_beats(self, user_content: str) -> str:
        return json.dumps(
            [
                {
                    "index": 1,
                    "scene": "开篇场景",
                    "goal": "建立本章基调",
                    "conflict": "突发变故",
                    "outcome": "主角做出选择",
                },
                {
                    "index": 2,
                    "scene": "冲突升级",
                    "goal": "推进主线",
                    "conflict": "对手阻挠",
                    "outcome": "获得线索",
                },
                {
                    "index": 3,
                    "scene": "章末",
                    "goal": "留下悬念",
                    "conflict": "意外发现",
                    "outcome": "引出下章",
                },
            ],
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
