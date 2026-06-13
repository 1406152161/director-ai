# @author zhangzhihao
"""小说规划：大纲 + 人物 + Story Bible 初始化。"""

from app.core.config import Settings, get_settings
from app.novel.prompts import build_plan_system_prompt, genre_label
from app.providers.base import Message
from app.providers.registry import get_novel_llm_provider
from app.utils.json_parse import parse_json_from_llm


class NovelPlanService:
    """调用 LLM 生成小说规划 JSON。"""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._llm = get_novel_llm_provider(self._settings)

    async def generate_plan(self, premise: str, genre: str) -> dict:
        """返回规划 JSON：title, synopsis, world, characters, outline。"""
        system = build_plan_system_prompt(genre)
        user = (
            f"题材：{genre_label(genre)}\n"
            f"用户创意：{premise}\n"
            "请输出完整 JSON，outline 至少 8 章。"
        )
        raw = await self._llm.chat(
            [Message("system", system), Message("user", user)],
            max_tokens=8192,
        )
        plan = parse_json_from_llm(raw)
        outline = plan.get("outline") or []
        if len(outline) < 8:
            raise ValueError(f"规划大纲不足 8 章，实际 {len(outline)} 章")
        return plan
