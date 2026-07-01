# @author zhangzhihao
"""卷/弧/全书滚动摘要。"""

import json

from app.novel.prompts import ROLLING_SUMMARY_MARKER, build_rolling_summary_system_prompt
from app.providers.base import Message
from app.providers.registry import get_novel_llm_provider
from app.services.novel_memory_service import parse_bible
from app.utils.json_parse import parse_json_from_llm


class NovelSummaryService:
    """每章完成后更新 rolling_summary。"""

    def __init__(self) -> None:
        self._llm = get_novel_llm_provider()

    async def update_rolling_summary(
        self,
        bible_json: str,
        chapter_index: int,
        chapter_summary: str,
    ) -> str:
        bible = parse_bible(bible_json)
        meta = dict(bible.get("meta") or {})
        current = meta.get("rolling_summary") or {}

        system = build_rolling_summary_system_prompt()
        user = (
            f"第{chapter_index}章摘要：{chapter_summary}\n"
            f"现有滚动摘要：{json.dumps(current, ensure_ascii=False)}\n"
            "请输出更新后的 JSON。"
        )
        raw = await self._llm.chat(
            [Message("system", system), Message("user", user)],
            max_tokens=2048,
        )
        if ROLLING_SUMMARY_MARKER not in system:
            pass
        data = parse_json_from_llm(raw)
        meta["rolling_summary"] = {
            "book": data.get("book") or current.get("book", ""),
            "volume": data.get("volume") or current.get("volume", ""),
            "arc": data.get("arc") or current.get("arc", ""),
        }
        bible["meta"] = meta
        return json.dumps(bible, ensure_ascii=False)
