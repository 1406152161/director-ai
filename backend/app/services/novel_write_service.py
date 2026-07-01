# @author zhangzhihao
"""小说章节写作与摘要生成。"""

from typing import Any

from app.core.config import Settings, get_settings
from app.novel.prompts import (
    build_rewrite_system_prompt,
    build_summary_system_prompt,
    build_write_system_prompt,
    genre_label,
)
from app.novel.utils import count_chinese_words
from app.providers.base import Message
from app.providers.registry import get_novel_llm_provider
from app.services.novel_prompt_builder import (
    build_layered_rewrite_context,
    build_layered_write_context,
)


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
        beats: list[dict[str, Any]] | None = None,
        foreshadowing: list[dict[str, Any]] | None = None,
        entities_prompt: str = "",
        framework_snippets: list[str] | None = None,
        plant_snippets: list[dict[str, Any]] | None = None,
    ) -> tuple[str, str, int]:
        """写一章正文并生成摘要，返回 (content, summary, word_count)。"""
        idx = chapter_outline.get("index", 1)
        user_prompt = build_layered_write_context(
            premise=premise,
            genre_label=genre_label(genre),
            bible=bible,
            chapter_index=idx,
            outline=chapter_outline,
            beats=beats or [],
            foreshadowing=foreshadowing or [],
            entities_prompt=entities_prompt,
            framework_snippets=framework_snippets or [],
            memory_snippets=memory_snippets,
            prev_tail=prev_tail,
            plant_snippets=plant_snippets or [],
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
        title = chapter_outline.get("title", f"第{idx}章")
        summary = await self._generate_summary(title, content)
        return content, summary, word_count

    async def rewrite_chapter(
        self,
        premise: str,
        genre: str,
        bible: dict,
        chapter_outline: dict,
        memory_snippets: list[str],
        prev_tail: str,
        beats: list[dict[str, Any]] | None,
        foreshadowing: list[dict[str, Any]] | None,
        previous_content: str,
        issues: list[str],
        entities_prompt: str = "",
        framework_snippets: list[str] | None = None,
        plant_snippets: list[dict[str, Any]] | None = None,
    ) -> tuple[str, str, int]:
        """校验失败后修订重写。"""
        idx = chapter_outline.get("index", 1)
        title = chapter_outline.get("title", f"第{idx}章")
        layered = build_layered_write_context(
            premise=premise,
            genre_label=genre_label(genre),
            bible=bible,
            chapter_index=idx,
            outline=chapter_outline,
            beats=beats or [],
            foreshadowing=foreshadowing or [],
            entities_prompt=entities_prompt,
            framework_snippets=framework_snippets or [],
            memory_snippets=memory_snippets,
            prev_tail=prev_tail,
            plant_snippets=plant_snippets or [],
        )
        user_prompt = build_layered_rewrite_context(
            premise=premise,
            genre_label=genre_label(genre),
            layered_base=layered,
            issues=issues,
            previous_content=previous_content,
        )
        system = build_rewrite_system_prompt(
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
