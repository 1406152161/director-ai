# @author zhangzhihao
"""小说规划 JSON 校验。"""

from typing import Any

from app.novel.plan_constants import (
    ABSOLUTE_MAX_CHAPTERS,
    MIN_OUTLINE_CHAPTERS,
    USER_TARGET_FLEX,
)


def clamp_total_chapters(total: int | None, user_target: int | None = None) -> int:
    """将章数限制在合法区间；有用户目标时允许 ±USER_TARGET_FLEX。"""
    if total is None or total < MIN_OUTLINE_CHAPTERS:
        total = user_target or MIN_OUTLINE_CHAPTERS
    total = max(MIN_OUTLINE_CHAPTERS, min(int(total), ABSOLUTE_MAX_CHAPTERS))
    if user_target is not None:
        low = max(MIN_OUTLINE_CHAPTERS, user_target - USER_TARGET_FLEX)
        high = min(ABSOLUTE_MAX_CHAPTERS, user_target + USER_TARGET_FLEX)
        total = max(low, min(total, high))
    return total


def validate_total_chapters(total: int, user_target: int | None = None) -> None:
    if total < MIN_OUTLINE_CHAPTERS:
        raise ValueError(f"全书章数不足 {MIN_OUTLINE_CHAPTERS} 章，实际 {total} 章")
    if total > ABSOLUTE_MAX_CHAPTERS:
        raise ValueError(f"全书章数超过上限 {ABSOLUTE_MAX_CHAPTERS} 章")
    if user_target is not None:
        low = max(MIN_OUTLINE_CHAPTERS, user_target - USER_TARGET_FLEX)
        high = min(ABSOLUTE_MAX_CHAPTERS, user_target + USER_TARGET_FLEX)
        if not (low <= total <= high):
            raise ValueError(
                f"AI 建议章数 {total} 须在用户目标 {user_target}±{USER_TARGET_FLEX}（{low}–{high}）内"
            )


def validate_plan(plan: dict[str, Any], user_target: int | None = None) -> None:
    """校验 L0 合并结果（outline 可在 DB，此处仅校验 meta 与伏笔/卷弧）。"""
    outline = plan.get("outline") or []
    total = plan.get("meta", {}).get("total_chapters") or len(outline) or 0
    validate_total_chapters(int(total), user_target)

    if outline and len(outline) > ABSOLUTE_MAX_CHAPTERS:
        raise ValueError(f"规划大纲超过上限 {ABSOLUTE_MAX_CHAPTERS} 章")

    if user_target is not None and outline:
        if len(outline) > total:
            raise ValueError("大纲章数超过 AI 确定的全书章数")

    total = int(total)
    for fs in plan.get("foreshadowing") or []:
        plant = fs.get("plant_chapter")
        resolve = fs.get("resolve_chapter")
        if plant is not None and (plant < 1 or plant > total):
            raise ValueError(f"伏笔 {fs.get('id')} 埋设章 {plant} 超出范围 1–{total}")
        if resolve is not None and (resolve < 1 or resolve > total):
            raise ValueError(f"伏笔 {fs.get('id')} 回收章 {resolve} 超出范围 1–{total}")
        if plant and resolve and plant > resolve:
            raise ValueError(f"伏笔 {fs.get('id')} 埋设章不能晚于回收章")

    for item in outline:
        idx = item.get("index")
        if idx is None or idx < 1 or idx > total:
            raise ValueError(f"大纲 index 无效: {idx}")


def validate_outline_batch(
    items: list[dict[str, Any]],
    chapter_from: int,
    chapter_to: int,
    total: int,
    volume_arc_ids: set[str] | None = None,
) -> None:
    """校验单批 outline 条目。"""
    expected = set(range(chapter_from, chapter_to + 1))
    got = {item.get("index") for item in items}
    if got != expected:
        missing = expected - got
        extra = got - expected
        raise ValueError(
            f"批次 {chapter_from}–{chapter_to} index 不完整，缺 {sorted(missing)} 多 {sorted(extra - expected)}"
        )
    for item in items:
        idx = item.get("index")
        if idx < 1 or idx > total:
            raise ValueError(f"章号 {idx} 超出全书 {total}")
        if volume_arc_ids is not None:
            arc = item.get("arc_id")
            if arc and str(arc) not in volume_arc_ids:
                raise ValueError(f"第 {idx} 章 arc_id {arc} 不在卷弧表中")


def collect_arc_ids(plan: dict[str, Any]) -> set[str]:
    ids: set[str] = set()
    for vol in plan.get("volumes") or []:
        if vol.get("id"):
            ids.add(str(vol["id"]))
        for arc in vol.get("arcs") or []:
            if arc.get("id"):
                ids.add(str(arc["id"]))
    return ids
