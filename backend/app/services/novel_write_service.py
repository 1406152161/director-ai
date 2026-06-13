# @author zhangzhihao
"""小说章节写作与摘要生成。"""

from app.core.config import Settings, get_settings
from app.novel.prompts import build_summary_system_prompt, build_write_system_prompt, genre_label
from app.novel.utils import count_chinese_words
from app.providers.base import Message
from app.providers.registry import get_novel_llm_provider
from app.services.novel_memory_service import bible_to_prompt_summary


class NovelWriteService:
    """单章正文与摘要写作。"""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._llm = get_novel_llm_provider(self._settings)

    async def write_chapter(
        self,
        premise: str,
        genre: str,
        bible: dict,
        chapter_outline: dict,
        memory_snippets: list[str],
        prev_tail: str = "",
    ) -> tuple[str, str, int]:
        """写一章正文并生成摘要，返回 (content, summary, word_count)。"""
        idx = chapter_outline.get("index", 1)
        title = chapter_outline.get("title", f"第{idx}章")
        summary_hint = chapter_outline.get("summary", "")

        bible_ctx = bible_to_prompt_summary(bible)
        memory_ctx = "\n".join(f"- {s}" for s in memory_snippets) if memory_snippets else "（暂无）"
        prev_ctx = prev_tail[-500:] if prev_tail else "（首章无前文）"

        user_prompt = (
            f"创意：{premise}\n"
            f"题材：{genre_label(genre)}\n\n"
            f"Story Bible：\n{bible_ctx}\n\n"
            f"相关记忆片段：\n{memory_ctx}\n\n"
            f"本章大纲：第{idx}章《{title}》\n{summary_hint}\n\n"
            f"上一章末尾：\n{prev_ctx}\n\n"
            f"请撰写第{idx}章正文。"
        )

        system = build_write_system_prompt(
            genre,
            self._settings.novel_target_words_min,
            self._settings.novel_target_words_max,
        )
        content = await self._llm.chat(
            [Message("system", system), Message("user", user_prompt)],
            max_tokens=8192,
        )
        content = content.strip()
        word_count = count_chinese_words(content)

        summary = await self._generate_summary(title, content)
        return content, summary, word_count

    async def _generate_summary(self, title: str, content: str) -> str:
        system = build_summary_system_prompt()
        user = f"章节标题：{title}\n\n正文：\n{content[:4000]}"
        return (await self._llm.chat(
            [Message("system", system), Message("user", user)],
            max_tokens=1024,
        )).strip()
