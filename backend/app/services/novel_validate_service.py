# @author zhangzhihao
"""章节写后质量校验。"""

import json
from dataclasses import dataclass
from typing import Any

from app.core.config import Settings, get_settings
from app.novel.prompts import VALIDATE_MARKER, build_validate_system_prompt
from app.providers.base import Message
from app.providers.registry import get_novel_llm_provider
from app.services.novel_memory_service import beats_to_prompt, foreshadowing_to_prompt
from app.utils.json_parse import parse_json_from_llm

PASS_SCORE = 70
MIN_CONTENT_CHARS = 50


@dataclass
class ValidationResult:
    passed: bool
    score: int
    issues: list[str]


class NovelValidateService:
    """规则 + LLM 写后校验。"""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._llm = get_novel_llm_provider(self._settings)

    def validate_rules(
        self,
        content: str,
        word_count: int,
        outline: dict[str, Any],
    ) -> list[str]:
        issues: list[str] = []
        if len(content.strip()) < MIN_CONTENT_CHARS:
            issues.append("正文过短或为空")
        target_min = self._settings.novel_target_words_min
        target_max = self._settings.novel_target_words_max
        if word_count < target_min * 0.15:
            issues.append(f"字数明显不足（约 {word_count} 字，目标 {target_min}–{target_max}）")
        if not outline.get("summary"):
            issues.append("本章大纲 summary 缺失，无法对照校验")
        return issues

    async def validate_chapter(
        self,
        genre: str,
        chapter_index: int,
        title: str,
        content: str,
        summary: str,
        word_count: int,
        outline: dict[str, Any],
        beats: list[dict[str, Any]],
        foreshadowing: list[dict[str, Any]],
        bible_summary: str,
    ) -> ValidationResult:
        rule_issues = self.validate_rules(content, word_count, outline)
        hard_fail = any("过短" in i or "为空" in i for i in rule_issues)

        llm_result = await self._llm_validate(
            genre,
            chapter_index,
            title,
            content,
            outline,
            beats,
            foreshadowing,
            bible_summary,
        )
        all_issues = rule_issues + llm_result.issues
        passed = (
            not hard_fail
            and llm_result.passed
            and llm_result.score >= PASS_SCORE
        )
        score = llm_result.score if not hard_fail else min(llm_result.score, PASS_SCORE - 1)
        return ValidationResult(passed=passed, score=score, issues=all_issues)

    async def _llm_validate(
        self,
        genre: str,
        chapter_index: int,
        title: str,
        content: str,
        outline: dict[str, Any],
        beats: list[dict[str, Any]],
        foreshadowing: list[dict[str, Any]],
        bible_summary: str,
    ) -> ValidationResult:
        system = build_validate_system_prompt(genre)
        user = (
            f"第{chapter_index}章《{title}》\n"
            f"大纲：{outline.get('summary', '')}\n"
            f"钩子：{outline.get('hook', '')}\n"
            f"场景 beat：\n{beats_to_prompt(beats)}\n"
            f"伏笔任务：\n{foreshadowing_to_prompt(foreshadowing, chapter_index)}\n"
            f"Story Bible 摘要：\n{bible_summary}\n\n"
            f"正文：\n{content[:6000]}\n\n"
            "请输出校验 JSON。"
        )
        raw = await self._llm.chat(
            [Message("system", system), Message("user", user)],
            max_tokens=2048,
        )
        data = parse_json_from_llm(raw)
        issues = [str(i) for i in (data.get("issues") or [])]
        return ValidationResult(
            passed=bool(data.get("passed", False)),
            score=int(data.get("score", 0)),
            issues=issues,
        )

    @staticmethod
    def issues_to_json(issues: list[str]) -> str:
        return json.dumps(issues, ensure_ascii=False)
