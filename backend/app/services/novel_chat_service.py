# @author zhangzhihao
"""小说改稿对话：merge Story Bible / outline。"""

from app.core.config import Settings, get_settings
from app.novel.prompts import build_chat_system_prompt
from app.providers.base import Message
from app.providers.registry import get_novel_llm_provider
from app.services.novel_memory_service import merge_bible_updates, parse_bible
from app.utils.json_parse import parse_json_from_llm


class NovelChatService:
    """侧栏改稿对话。"""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._llm = get_novel_llm_provider(self._settings)

    async def chat(self, bible_json: str, message: str) -> tuple[str, dict]:
        """返回 (assistant_reply, merged_bible)。"""
        bible = parse_bible(bible_json)
        system = build_chat_system_prompt()
        user = (
            f"当前 Story Bible：\n{bible_json}\n\n"
            f"用户改稿意见：{message}"
        )
        raw = await self._llm.chat(
            [Message("system", system), Message("user", user)],
            max_tokens=4096,
        )
        data = parse_json_from_llm(raw)
        reply = data.get("reply", "已收到您的改稿意见。")
        updates = data.get("updates") or {}
        merged = merge_bible_updates(bible, updates)
        return reply, merged
