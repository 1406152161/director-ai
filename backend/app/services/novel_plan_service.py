# @author zhangzhihao
"""小说规划：L0 宏规划 → L1 骨架分批 → L2 近端详细（支持 checkpoint）。"""

import json
import logging
from typing import Any

from app.core.config import Settings, get_settings
from app.novel.plan_checkpoint import PlanCheckpointHandlers
from app.novel.plan_constants import (
    L1_BATCH_SIZE,
    L2_BATCH_SIZE,
    L2_INITIAL_WINDOW,
    L2_EXPAND_AHEAD,
    USER_TARGET_FLEX,
)
from app.novel.plan_validate import (
    clamp_total_chapters,
    collect_arc_ids,
    validate_outline_batch,
    validate_total_chapters,
)
from app.novel.prompts import (
    build_plan_detail_system_prompt,
    build_plan_skeleton_system_prompt,
    build_plan_world_system_prompt,
    genre_label,
)
from app.providers.base import Message
from app.providers.registry import get_novel_llm_provider
from app.utils.json_parse import parse_json_from_llm

logger = logging.getLogger(__name__)

_RETRY_HINT = (
    "上次输出不是合法 JSON 或已被截断。请仅重新输出完整 JSON，"
    "字符串内禁止使用未转义的英文双引号，内容精简。"
)


class NovelPlanService:
    """调用 LLM 生成分层规划。"""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._llm = get_novel_llm_provider(self._settings)

    async def generate_plan(
        self,
        premise: str,
        genre: str,
        *,
        target_chapters: int | None = None,
        handlers: PlanCheckpointHandlers | None = None,
    ) -> dict:
        return await self.execute_plan(
            premise,
            genre,
            target_chapters=target_chapters,
            world_plan=None,
            handlers=handlers,
        )

    async def execute_plan(
        self,
        premise: str,
        genre: str,
        *,
        target_chapters: int | None = None,
        world_plan: dict[str, Any] | None = None,
        handlers: PlanCheckpointHandlers | None = None,
    ) -> dict:
        h = handlers or PlanCheckpointHandlers()
        resume = h.resume_state or {}

        if world_plan is None:
            world_plan = await self._generate_l0(premise, genre, target_chapters)
            if h.on_l0_complete:
                h.on_l0_complete(world_plan)

        total = int(world_plan.get("meta", {}).get("total_chapters") or 0)
        validate_total_chapters(total, target_chapters)

        l1_done = int(resume.get("l1_done_through") or 0)
        skeleton = list(h.initial_skeleton) if h.initial_skeleton else []
        if resume.get("phase") != "l2_detail" and l1_done < total:
            skeleton = await self._generate_l1_skeleton(
                premise,
                genre,
                world_plan,
                total,
                initial_skeleton=skeleton,
                start_chapter=l1_done + 1 if l1_done else 1,
                on_batch=h.on_l1_batch,
                on_progress=h.on_progress,
            )
            if h.on_l1_batch is None and h.on_progress:
                h.on_progress(75)

        l2_done = int(resume.get("l2_done_through") or 0)
        l2_to = min(L2_INITIAL_WINDOW, total)
        detailed: list[dict] = []
        if l2_done < l2_to:
            detailed = await self._generate_l2_detail(
                premise,
                genre,
                world_plan,
                skeleton,
                max(1, l2_done + 1) if l2_done else 1,
                l2_to,
                on_batch=h.on_l2_batch,
            )

        outline = self._merge_outline_layers(skeleton, detailed, total)
        world_plan.setdefault("meta", {})["l2_detail_to"] = l2_to
        world_plan["meta"]["outline_in_db"] = True
        world_plan["meta"]["target_chapters_user"] = target_chapters
        if target_chapters:
            world_plan["meta"]["chapter_flex_range"] = [
                max(8, target_chapters - USER_TARGET_FLEX),
                target_chapters + USER_TARGET_FLEX,
            ]
        return {**world_plan, "outline": outline}

    async def expand_l2_detail(
        self,
        premise: str,
        genre: str,
        world_plan: dict,
        skeleton: list[dict],
        chapter_from: int,
        chapter_to: int,
    ) -> list[dict]:
        return await self._generate_l2_detail(
            premise, genre, world_plan, skeleton, chapter_from, chapter_to
        )

    async def _generate_l0(
        self,
        premise: str,
        genre: str,
        target_chapters: int | None,
    ) -> dict:
        if target_chapters:
            chapter_hint = (
                f"用户目标 {target_chapters} 章；请根据故事体量在 "
                f"{target_chapters - USER_TARGET_FLEX}–{target_chapters + USER_TARGET_FLEX} "
                f"之间确定 meta.total_chapters，并填写 chapter_count_reason"
            )
        else:
            chapter_hint = "用户未指定章数，请根据创意建议合理 total_chapters（通常 40–200）"

        world_system = build_plan_world_system_prompt(genre)
        world_user = (
            f"题材：{genre_label(genre)}\n"
            f"用户创意：{premise}\n"
            f"目标章数：{chapter_hint}\n"
            "请输出 L0 JSON（含 meta.total_chapters）。"
        )
        world_raw = await self._llm.chat(
            [Message("system", world_system), Message("user", world_user)],
            max_tokens=8192,
        )
        world_plan = await self._parse_json_with_retry(world_system, world_user, world_raw)

        total = world_plan.get("meta", {}).get("total_chapters")
        if target_chapters:
            total = clamp_total_chapters(total, target_chapters)
        else:
            total = clamp_total_chapters(total, None)
        world_plan.setdefault("meta", {})["total_chapters"] = total
        return world_plan

    async def _generate_l1_skeleton(
        self,
        premise: str,
        genre: str,
        world_plan: dict,
        total: int,
        *,
        initial_skeleton: list | None = None,
        start_chapter: int = 1,
        on_batch=None,
        on_progress=None,
    ) -> list[dict]:
        skeleton: list[dict] = list(initial_skeleton or [])
        arc_ids = collect_arc_ids(world_plan)
        system = build_plan_skeleton_system_prompt(genre)
        world_summary = self._world_summary(world_plan)

        chapter_from = start_chapter
        while chapter_from <= total:
            chapter_to = min(chapter_from + L1_BATCH_SIZE - 1, total)
            locked = skeleton.copy()
            arc_contract = self._arc_contract(world_plan, chapter_from, chapter_to)
            anchors = skeleton[-3:] if skeleton else []

            user = (
                f"题材：{genre_label(genre)}\n"
                f"用户创意：{premise}\n"
                f"全书共 {total} 章。本次仅输出第 {chapter_from}–{chapter_to} 章 **骨架** outline。\n"
                f"世界观与卷弧：\n{json.dumps(world_summary, ensure_ascii=False)}\n"
                f"弧段契约：\n{json.dumps(arc_contract, ensure_ascii=False)}\n"
                f"衔接锚点（前序章节，须连贯）：\n{json.dumps(anchors, ensure_ascii=False)}\n"
                f"锁定前缀（不可修改）：\n{json.dumps(locked, ensure_ascii=False)}\n"
                f"index 必须连续覆盖 {chapter_from}–{chapter_to}，不要 hook。"
            )
            raw = await self._llm.chat(
                [Message("system", system), Message("user", user)],
                max_tokens=8192,
            )
            data = await self._parse_json_with_retry(system, user, raw)
            batch = data if isinstance(data, list) else data.get("outline") or []
            validate_outline_batch(batch, chapter_from, chapter_to, total, arc_ids)
            skeleton.extend(batch)
            if on_batch:
                on_batch(batch, chapter_to)
            if on_progress:
                pct = min(75, int(75 * chapter_to / total))
                on_progress(pct)
            chapter_from = chapter_to + 1

        skeleton.sort(key=lambda x: x.get("index", 0))
        return skeleton

    async def _generate_l2_detail(
        self,
        premise: str,
        genre: str,
        world_plan: dict,
        skeleton: list[dict],
        chapter_from: int,
        chapter_to: int,
        on_batch=None,
    ) -> list[dict]:
        sk_map = {item["index"]: item for item in skeleton}
        detailed: list[dict] = []
        system = build_plan_detail_system_prompt(genre)
        world_summary = self._world_summary(world_plan)
        arc_ids = collect_arc_ids(world_plan)

        start = chapter_from
        while start <= chapter_to:
            end = min(start + L2_BATCH_SIZE - 1, chapter_to)
            sk_batch = [sk_map[i] for i in range(start, end + 1) if i in sk_map]
            anchors = [detailed[-1] if detailed else sk_map.get(start - 1)]
            anchors = [a for a in anchors if a]

            user = (
                f"题材：{genre_label(genre)}\n"
                f"用户创意：{premise}\n"
                f"请在下列骨架上扩写第 {start}–{end} 章 **详细** outline（含 hook）。\n"
                f"卷弧摘要：\n{json.dumps(world_summary, ensure_ascii=False)}\n"
                f"骨架：\n{json.dumps(sk_batch, ensure_ascii=False)}\n"
                f"上一章衔接：\n{json.dumps(anchors, ensure_ascii=False)}"
            )
            raw = await self._llm.chat(
                [Message("system", system), Message("user", user)],
                max_tokens=8192,
            )
            data = await self._parse_json_with_retry(system, user, raw)
            batch = data if isinstance(data, list) else data.get("outline") or []
            validate_outline_batch(
                batch, start, end, int(world_plan["meta"]["total_chapters"]), arc_ids
            )
            detailed.extend(batch)
            if on_batch:
                on_batch(batch, end)
            start = end + 1

        return detailed

    @staticmethod
    def _merge_outline_layers(
        skeleton: list[dict],
        detailed: list[dict],
        total: int,
    ) -> list[dict]:
        sk = {item["index"]: dict(item) for item in skeleton}
        for item in detailed:
            idx = item.get("index")
            if idx in sk:
                sk[idx].update(item)
                sk[idx]["detail_level"] = "detailed"
            else:
                sk[idx] = {**item, "detail_level": "detailed"}
        for idx in range(1, total + 1):
            if idx in sk and "detail_level" not in sk[idx]:
                sk[idx]["detail_level"] = "skeleton"
        return [sk[i] for i in sorted(sk.keys()) if i <= total]

    @staticmethod
    def _world_summary(world_plan: dict) -> dict:
        return {
            "title": world_plan.get("title"),
            "synopsis": world_plan.get("synopsis"),
            "volumes": world_plan.get("volumes"),
            "meta": world_plan.get("meta"),
        }

    @staticmethod
    def _arc_contract(world_plan: dict, chapter_from: int, chapter_to: int) -> list[dict]:
        contracts = []
        for vol in world_plan.get("volumes") or []:
            for arc in vol.get("arcs") or []:
                af = arc.get("chapter_from") or 0
                at = arc.get("chapter_to") or 0
                if at < chapter_from or af > chapter_to:
                    continue
                contracts.append(
                    {
                        "volume_id": vol.get("id"),
                        "arc_id": arc.get("id"),
                        "title": arc.get("title"),
                        "conflict": arc.get("conflict"),
                        "chapter_from": af,
                        "chapter_to": at,
                    }
                )
        return contracts

    async def _parse_json_with_retry(self, system: str, user: str, raw: str) -> dict:
        messages = [Message("system", system), Message("user", user)]
        try:
            return parse_json_from_llm(raw)
        except ValueError as first_exc:
            logger.warning("规划 JSON 首次解析失败，将重试: %s", first_exc)
            messages.append(Message("assistant", content=raw))
            messages.append(Message("user", content=_RETRY_HINT))
            retry_raw = await self._llm.chat(messages, max_tokens=8192)
            try:
                return parse_json_from_llm(retry_raw)
            except ValueError as retry_exc:
                logger.error("规划 JSON 解析失败，片段: %s", retry_raw[:500])
                raise retry_exc from first_exc


def l2_expand_range(last_written: int, total: int) -> tuple[int, int] | None:
    need_from = last_written + 1
    need_to = min(last_written + L2_EXPAND_AHEAD, total)
    return (need_from, need_to) if need_from <= total else None
