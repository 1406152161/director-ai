# @author zhangzhihao
"""分层 Mandatory Prompt 组装。"""

from typing import Any

from app.services.novel_memory_service import (
    beats_to_prompt,
    bible_to_prompt_summary,
    foreshadowing_to_prompt,
)


def get_rolling_summary(bible: dict[str, Any]) -> dict[str, str]:
    meta = bible.get("meta") or {}
    rs = meta.get("rolling_summary") or {}
    return {
        "book": rs.get("book", ""),
        "volume": rs.get("volume", ""),
        "arc": rs.get("arc", ""),
    }


def rolling_summary_to_prompt(bible: dict[str, Any]) -> str:
    rs = get_rolling_summary(bible)
    parts = []
    if rs.get("book"):
        parts.append(f"全书摘要：{rs['book']}")
    if rs.get("volume"):
        parts.append(f"当前卷：{rs['volume']}")
    if rs.get("arc"):
        parts.append(f"当前弧：{rs['arc']}")
    return "\n".join(parts) if parts else "（暂无滚动摘要）"


def plant_snippets_to_prompt(snippets: list[dict[str, Any]]) -> str:
    if not snippets:
        return "（本章无埋设章原文对照）"
    lines = []
    for sn in snippets:
        lines.append(
            f"- 伏笔 [{sn.get('id', '?')}] 埋设于第{sn.get('plant_chapter')}章：\n"
            f"{sn.get('excerpt', '')[:800]}"
        )
    return "\n".join(lines)


def build_layered_write_context(
    *,
    premise: str,
    genre_label: str,
    bible: dict[str, Any],
    chapter_index: int,
    outline: dict[str, Any],
    beats: list[dict[str, Any]],
    foreshadowing: list[dict[str, Any]],
    entities_prompt: str,
    framework_snippets: list[str],
    memory_snippets: list[str],
    prev_tail: str,
    plant_snippets: list[dict[str, Any]],
) -> str:
    """P0 Mandatory + P1/P2 补充，供写作/重写 user prompt 使用。"""
    idx = chapter_index
    title = outline.get("title", f"第{idx}章")
    p0 = (
        f"=== P0 必须遵守 ===\n"
        f"第{idx}章《{title}》大纲：{outline.get('summary', '')}\n"
        f"章末钩子：{outline.get('hook', '')}\n"
        f"场景 beat：\n{beats_to_prompt(beats)}\n"
        f"伏笔任务：\n{foreshadowing_to_prompt(foreshadowing, idx)}\n"
        f"埋设章原文对照：\n{plant_snippets_to_prompt(plant_snippets)}\n"
        f"实体状态（confirmed）：\n{entities_prompt}\n"
    )
    p1 = (
        f"=== P1 强相关 ===\n"
        f"Story Bible：\n{bible_to_prompt_summary(bible)}\n"
        f"滚动摘要：\n{rolling_summary_to_prompt(bible)}\n"
        f"上一章末尾：\n{prev_tail[-500:] if prev_tail else '（首章无前文）'}\n"
    )
    fw = "\n".join(f"- {s}" for s in framework_snippets) if framework_snippets else "（无）"
    mem = "\n".join(f"- {s}" for s in memory_snippets) if memory_snippets else "（无）"
    p2 = f"=== P2 检索补充 ===\n框架检索：\n{fw}\n相关记忆：\n{mem}\n"

    return (
        f"创意：{premise}\n题材：{genre_label}\n\n"
        f"{p0}\n{p1}\n{p2}\n"
        f"请撰写第{idx}章正文。"
    )


def build_layered_rewrite_context(
    *,
    premise: str,
    genre_label: str,
    layered_base: str,
    issues: list[str],
    previous_content: str,
) -> str:
    issue_text = "\n".join(f"- {i}" for i in issues) if issues else "（无）"
    return (
        f"{layered_base}\n\n"
        f"=== 责编问题清单 ===\n{issue_text}\n\n"
        f"上一版正文（需修订）：\n{previous_content[:4000]}\n\n"
        "请重写整章正文。"
    )
