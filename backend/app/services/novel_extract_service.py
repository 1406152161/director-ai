# @author zhangzhihao
"""写后结构化抽取。"""

import json
from typing import Any

from app.novel.prompts import EXTRACT_MARKER, build_extract_system_prompt
from app.providers.base import Message
from app.providers.registry import get_novel_llm_provider
from app.services.novel_memory_service import (
    merge_bible_updates,
    parse_bible,
    update_foreshadowing_after_chapter,
)
from app.utils.json_parse import parse_json_from_llm


def _bible_context_for_extract(bible_json: str) -> str:
    """核心设定完整保留，大纲仅取前 50 章摘要。"""
    bible = parse_bible(bible_json)
    outline = bible.get("outline") or []
    outline_summary = json.dumps(outline[:50], ensure_ascii=False)[:3000]
    core = {k: v for k, v in bible.items() if k != "outline"}
    bible_context = json.dumps(core, ensure_ascii=False)
    return f"{bible_context}\n\n大纲摘要（前50章）：\n{outline_summary}"


class NovelExtractService:
    """章节完成后抽取事实/实体/伏笔状态。"""

    def __init__(self) -> None:
        self._llm = get_novel_llm_provider()

    async def extract_after_chapter(
        self,
        chapter_index: int,
        title: str,
        content: str,
        summary: str,
        bible_json: str,
    ) -> tuple[dict[str, Any], list[dict], list[dict], list[str]]:
        """返回 (merged_bible, entity_updates, fs_updates, new_facts)。"""
        system = build_extract_system_prompt()
        bible_context = _bible_context_for_extract(bible_json)
        user = (
            f"第{chapter_index}章《{title}》\n"
            f"摘要：{summary}\n\n正文：\n{content[:5000]}\n\n"
            f"当前 Bible：\n{bible_context}\n"
        )
        raw = await self._llm.chat(
            [Message("system", system), Message("user", user)],
            max_tokens=2048,
        )
        if EXTRACT_MARKER not in system:
            pass
        data = parse_json_from_llm(raw)
        bible = parse_bible(bible_json)
        facts = [f for f in (data.get("facts") or []) if f]
        if facts:
            bible = merge_bible_updates(bible, {"facts": facts})
        for fs_up in data.get("foreshadowing_updates") or []:
            fid = fs_up.get("id")
            new_status = fs_up.get("status")
            if not fid or not new_status:
                continue
            updated = []
            for fs in bible.get("foreshadowing") or []:
                item = dict(fs)
                if item.get("id") == fid:
                    item["status"] = new_status
                updated.append(item)
            bible["foreshadowing"] = updated
        bible = update_foreshadowing_after_chapter(bible, chapter_index)
        entity_updates = data.get("entity_updates") or []
        return bible, entity_updates, data.get("foreshadowing_updates") or [], facts
