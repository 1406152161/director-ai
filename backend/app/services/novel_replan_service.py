# @author zhangzhihao
"""未写章节大纲动态调整（Replan）。"""

import json

from sqlalchemy.orm import Session

from app.novel.prompts import build_replan_system_prompt, genre_label
from app.providers.base import Message
from app.providers.registry import get_novel_llm_provider
from app.services.novel_memory_service import parse_bible
from app.services.novel_outline_service import NovelOutlineService
from app.utils.json_parse import parse_json_from_llm


class NovelReplanService:
    """根据已写内容调整未写 outline / 伏笔。"""

    def __init__(self) -> None:
        self._llm = get_novel_llm_provider()

    async def replan_unwritten(
        self,
        novel_id: str,
        db: Session,
        premise: str,
        genre: str,
        bible_json: str,
        last_written_index: int,
        written_summaries: list[str],
    ) -> tuple[list[dict], list[dict]]:
        bible = parse_bible(bible_json)
        outline_svc = NovelOutlineService(db)
        total = int(bible.get("meta", {}).get("total_chapters") or 0)
        outline_in_db = bool(bible.get("meta", {}).get("outline_in_db"))
        use_db = outline_in_db or outline_svc.count_by_level(novel_id) > 0

        if use_db and total > 0:
            locked = outline_svc.to_bible_outline(novel_id, 1, last_written_index)
            unwritten = outline_svc.to_bible_outline(novel_id, last_written_index + 1, total)
        else:
            locked = [
                o for o in (bible.get("outline") or []) if o.get("index", 0) <= last_written_index
            ]
            unwritten = [
                o for o in (bible.get("outline") or []) if o.get("index", 0) > last_written_index
            ]

        system = build_replan_system_prompt(genre)
        fs_json = json.dumps(bible.get("foreshadowing") or [], ensure_ascii=False)
        user = (
            f"题材：{genre_label(genre)}\n创意：{premise}\n"
            f"已写至第 {last_written_index} 章。\n"
            f"已写章节摘要：\n" + "\n".join(f"- {s}" for s in written_summaries[-10:]) + "\n"
            f"locked outline（不可改）：\n{json.dumps(locked, ensure_ascii=False)}\n"
            f"待调整 unwritten outline：\n{json.dumps(unwritten, ensure_ascii=False)}\n"
            f"当前 foreshadowing：\n{fs_json}\n"
            "请输出调整后的 unwritten outline 与 foreshadowing。"
        )
        raw = await self._llm.chat(
            [Message("system", system), Message("user", user)],
            max_tokens=8192,
        )
        data = parse_json_from_llm(raw)
        new_unwritten = data.get("outline") or unwritten
        new_unwritten = [
            o for o in new_unwritten if int(o.get("index", 0)) > last_written_index
        ]
        merged_outline = locked + sorted(new_unwritten, key=lambda x: x.get("index", 0))
        foreshadowing = data.get("foreshadowing") or bible.get("foreshadowing") or []
        return merged_outline, foreshadowing
