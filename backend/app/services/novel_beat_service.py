# @author zhangzhihao
"""单章场景 beat 生成。"""

import json
from typing import Any

from app.core.config import Settings, get_settings
from app.novel.prompts import build_beat_system_prompt, genre_label
from app.providers.base import Message
from app.providers.registry import get_novel_llm_provider
from app.utils.json_parse import parse_json_value_from_llm


class NovelBeatService:
    """为待写章节生成 3–6 个场景 beat。"""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._llm = get_novel_llm_provider(self._settings)

    async def generate_beats(
        self,
        premise: str,
        genre: str,
        bible: dict[str, Any],
        chapter_outline: dict[str, Any],
        foreshadowing: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        idx = chapter_outline.get("index", 1)
        title = chapter_outline.get("title", f"第{idx}章")
        system = build_beat_system_prompt(genre)
        user = (
            f"创意：{premise}\n"
            f"题材：{genre_label(genre)}\n"
            f"第{idx}章《{title}》大纲：{chapter_outline.get('summary', '')}\n"
            f"章末钩子：{chapter_outline.get('hook', '')}\n"
            f"本章相关伏笔：\n{json.dumps(foreshadowing, ensure_ascii=False)}\n"
            "请输出 beat JSON 数组。"
        )
        raw = await self._llm.chat(
            [Message("system", system), Message("user", user)],
            max_tokens=4096,
        )
        beats = parse_json_value_from_llm(raw)
        if isinstance(beats, dict):
            beats = beats.get("beats") or beats.get("items") or []
        if not isinstance(beats, list):
            raise ValueError("beat 规划结果不是数组")
        return beats
