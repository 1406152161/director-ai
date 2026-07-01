# @author zhangzhihao
"""小说生成编排：规划 → 写前 N 章 → 校验 → 记忆。"""

import json
import logging

from app.core.database import SessionLocal
from app.novel.plan_checkpoint import (
    PlanCheckpointHandlers,
    can_resume_planning,
    planning_state_from_meta,
)
from app.novel.plan_constants import L2_BATCH_SIZE, L2_INITIAL_WINDOW
from app.novel.plan_validate import validate_plan
from app.services.novel_beat_service import NovelBeatService
from app.services.novel_entity_service import NovelEntityService
from app.services.novel_framework_service import NovelFrameworkService
from app.services.novel_memory_service import (
    NovelMemoryService,
    bible_to_prompt_summary,
    foreshadowing_for_chapter,
    get_beats_for_chapter,
    parse_bible,
    save_beats_for_chapter,
)
from app.services.novel_outline_service import NovelOutlineService
from app.services.novel_plan_service import NovelPlanService, l2_expand_range
from app.services.novel_postwrite_service import NovelPostwriteService, get_plant_snippets
from app.services.novel_service import MAX_OUTLINE_INLINE_ITEMS, NovelService
from app.services.novel_validate_service import NovelValidateService
from app.services.novel_write_service import NovelWriteService

logger = logging.getLogger(__name__)


def _outline_entry(bible: dict, index: int) -> dict | None:
    for item in bible.get("outline") or []:
        if item.get("index") == index:
            return item
    return None


def _resolve_outline(
    outline_svc: NovelOutlineService,
    novel_id: str,
    index: int,
    bible: dict,
) -> dict | None:
    row = outline_svc.get_chapter(novel_id, index)
    if row:
        return NovelOutlineService.entry_for_writing(row, index)
    return _outline_entry(bible, index)


async def _ensure_l2_for_range(
    novel_id: str,
    chapter_from: int,
    chapter_to: int,
    novel_svc: NovelService,
    plan_svc: NovelPlanService,
    outline_svc: NovelOutlineService,
    framework_svc: NovelFrameworkService,
) -> None:
    """写作前确保区间内章纲已 L2 详细化。"""
    novel = novel_svc.get_novel(novel_id)
    if not novel:
        return
    bible = parse_bible(novel.bible_json)
    total = int(bible.get("meta", {}).get("total_chapters") or 0)
    chapter_to = min(chapter_to, total)
    needs = []
    for idx in range(chapter_from, chapter_to + 1):
        row = outline_svc.get_chapter(novel_id, idx)
        if not row or row.detail_level != "detailed" or not (row.hook or "").strip():
            needs.append(idx)
    if not needs:
        return

    from_i = min(needs)
    to_i = max(needs)
    skeleton = outline_svc.to_bible_outline(novel_id, 1, total)
    world_plan = {
        **bible,
        "title": novel.title,
        "synopsis": novel.synopsis,
    }
    detailed = await plan_svc.expand_l2_detail(
        novel.premise, novel.genre, world_plan, skeleton, from_i, to_i
    )
    outline_svc.upsert_batch(novel_id, detailed, detail_level="detailed")
    meta = bible.get("meta") or {}
    meta["l2_detail_to"] = max(int(meta.get("l2_detail_to") or 0), to_i)
    bible["meta"] = meta
    novel_svc.save_bible(novel_id, bible)
    bible_sync = dict(bible)
    bible_sync["outline"] = outline_svc.to_bible_outline(
        novel_id, 1, min(total, MAX_OUTLINE_INLINE_ITEMS)
    )
    framework_svc.sync_from_bible(novel_id, bible_sync)


async def _write_single_chapter(
    novel_id: str,
    chapter_index: int,
    novel_svc: NovelService,
    write_svc: NovelWriteService,
    memory_svc: NovelMemoryService,
    beat_svc: NovelBeatService,
    validate_svc: NovelValidateService,
    entity_svc: NovelEntityService,
    framework_svc: NovelFrameworkService,
    postwrite_svc: NovelPostwriteService,
    outline_svc: NovelOutlineService,
    plan_svc: NovelPlanService,
) -> bool:
    """写单章并校验。返回 True 表示通过；False 表示待复核。"""
    novel = novel_svc.get_novel(novel_id)
    if not novel:
        return False

    bible = parse_bible(novel_svc.get_novel(novel_id).bible_json)
    total = int(bible.get("meta", {}).get("total_chapters") or chapter_index)
    l2_window = l2_expand_range(chapter_index - 1, total)
    if l2_window:
        l2_from, l2_to = l2_window
    else:
        l2_from, l2_to = chapter_index, min(chapter_index + L2_BATCH_SIZE - 1, total)
    await _ensure_l2_for_range(
        novel_id,
        l2_from,
        l2_to,
        novel_svc,
        plan_svc,
        outline_svc,
        framework_svc,
    )
    bible = parse_bible(novel_svc.get_novel(novel_id).bible_json)
    outline = _resolve_outline(outline_svc, novel_id, chapter_index, bible)
    if not outline:
        raise ValueError(f"大纲中不存在第 {chapter_index} 章")

    title = outline.get("title", f"第{chapter_index}章")
    chapter = novel_svc.get_chapter(novel_id, chapter_index)
    if not chapter:
        chapter = novel_svc.create_chapter_placeholder(novel_id, chapter_index, title)

    novel_svc.set_chapter_status(chapter.id, "writing")

    prev_tail = ""
    if chapter_index > 1:
        prev = novel_svc.get_chapter(novel_id, chapter_index - 1)
        if prev and prev.content:
            prev_tail = prev.content

    fs_items = foreshadowing_for_chapter(bible, chapter_index)
    beats = get_beats_for_chapter(bible, chapter_index)
    if not beats:
        beats = await beat_svc.generate_beats(
            novel.premise, novel.genre, bible, outline, fs_items
        )
        bible = save_beats_for_chapter(bible, chapter_index, beats)
        novel_svc.save_bible(novel_id, bible)

    query = f"第{chapter_index}章 {title} {outline.get('summary', '')}"
    snippets = memory_svc.query_relevant(novel_id, query)
    framework_snippets = framework_svc.query_hybrid(novel_id, query, chapter_index)
    entities_prompt = entity_svc.entities_to_prompt(entity_svc.list_confirmed(novel_id))
    plant_snippets = get_plant_snippets(novel_svc, novel_id, fs_items, chapter_index)
    bible_summary = bible_to_prompt_summary(bible)

    write_kw = dict(
        premise=novel.premise,
        genre=novel.genre,
        bible=bible,
        chapter_outline=outline,
        memory_snippets=snippets,
        prev_tail=prev_tail,
        beats=beats,
        foreshadowing=fs_items,
        entities_prompt=entities_prompt,
        framework_snippets=framework_snippets,
        plant_snippets=plant_snippets,
    )

    content, summary, word_count = await write_svc.write_chapter(**write_kw)

    result = await validate_svc.validate_chapter(
        novel.genre,
        chapter_index,
        title,
        content,
        summary,
        word_count,
        outline,
        beats,
        fs_items,
        bible_summary,
    )

    if not result.passed:
        logger.info("第 %s 章校验未通过，尝试重写: %s", chapter_index, result.issues)
        content, summary, word_count = await write_svc.rewrite_chapter(
            **write_kw,
            previous_content=content,
            issues=result.issues,
        )
        result = await validate_svc.validate_chapter(
            novel.genre,
            chapter_index,
            title,
            content,
            summary,
            word_count,
            outline,
            beats,
            fs_items,
            bible_summary,
        )

    issues_json = validate_svc.issues_to_json(result.issues)

    if result.passed:
        novel_svc.save_chapter(
            chapter.id,
            title,
            content,
            summary,
            word_count,
            status="completed",
            validation_status="passed",
            validation_score=result.score,
            validation_issues=issues_json,
        )
        await postwrite_svc.finalize_chapter(novel_id, chapter_index, title, content, summary)
        return True

    novel_svc.save_chapter(
        chapter.id,
        title,
        content,
        summary,
        word_count,
        status="needs_review",
        validation_status="needs_review",
        validation_score=result.score,
        validation_issues=issues_json,
    )
    logger.warning("第 %s 章复核未通过: %s", chapter_index, result.issues)
    return False


async def _write_chapter_range(
    novel_id: str,
    start_index: int,
    count: int,
    novel_svc: NovelService,
    write_svc: NovelWriteService,
    memory_svc: NovelMemoryService,
    beat_svc: NovelBeatService,
    validate_svc: NovelValidateService,
    entity_svc: NovelEntityService,
    framework_svc: NovelFrameworkService,
    postwrite_svc: NovelPostwriteService,
    outline_svc: NovelOutlineService,
    plan_svc: NovelPlanService,
) -> bool:
    """从 start_index 起连续写 count 章，遇复核则停止。"""
    bible = parse_bible(novel_svc.get_novel(novel_id).bible_json)
    total = int(bible.get("meta", {}).get("total_chapters") or 0)
    if not total:
        total = outline_svc.count_by_level(novel_id) or len(bible.get("outline") or [])
    end_index = min(start_index + count - 1, total)
    written = 0
    span = end_index - start_index + 1
    for chapter_index in range(start_index, end_index + 1):
        if not _resolve_outline(outline_svc, novel_id, chapter_index, bible):
            if not outline_svc.get_chapter(novel_id, chapter_index):
                novel_svc.set_failed(novel_id, f"大纲已无第 {chapter_index} 章可写")
                return False
        ok = await _write_single_chapter(
            novel_id,
            chapter_index,
            novel_svc,
            write_svc,
            memory_svc,
            beat_svc,
            validate_svc,
            entity_svc,
            framework_svc,
            postwrite_svc,
            outline_svc,
            plan_svc,
        )
        written += 1
        progress = 20 + int(70 * written / span) if span else 100
        novel_svc.update_status(novel_id, "writing", progress)
        if not ok:
            novel_svc.set_review_required(novel_id, progress)
            return False
    return True


async def _write_initial_chapters(
    novel_id: str,
    novel_svc: NovelService,
    write_svc: NovelWriteService,
    memory_svc: NovelMemoryService,
    beat_svc: NovelBeatService,
    validate_svc: NovelValidateService,
    entity_svc: NovelEntityService,
    framework_svc: NovelFrameworkService,
    postwrite_svc: NovelPostwriteService,
    outline_svc: NovelOutlineService,
    plan_svc: NovelPlanService,
    count: int,
) -> bool:
    return await _write_chapter_range(
        novel_id,
        1,
        count,
        novel_svc,
        write_svc,
        memory_svc,
        beat_svc,
        validate_svc,
        entity_svc,
        framework_svc,
        postwrite_svc,
        outline_svc,
        plan_svc,
    )


def _build_services(db):
    novel_svc = NovelService(db)
    memory_svc = NovelMemoryService()
    return (
        novel_svc,
        NovelPlanService(),
        NovelWriteService(),
        memory_svc,
        NovelBeatService(),
        NovelValidateService(),
        NovelEntityService(db),
        NovelFrameworkService(db, memory_svc),
        NovelPostwriteService(db),
        NovelOutlineService(db),
    )


async def run_novel_generation(novel_id: str) -> None:
    db = SessionLocal()
    try:
        (
            novel_svc,
            plan_svc,
            write_svc,
            memory_svc,
            beat_svc,
            validate_svc,
            entity_svc,
            framework_svc,
            postwrite_svc,
            outline_svc,
        ) = _build_services(db)

        novel = novel_svc.get_novel(novel_id)
        if not novel:
            return

        bible = parse_bible(novel.bible_json)
        meta = bible.get("meta") or {}
        target_chapters = meta.get("target_chapters_user")
        state = planning_state_from_meta(meta)
        resume = can_resume_planning(meta) and bool(state.get("phase"))

        if not resume:
            outline_svc.delete_all(novel_id)

        l1_done = int(state.get("l1_done_through") or 0)
        total_ch = int(meta.get("total_chapters") or 0)
        if resume and state.get("phase") == "l2_detail" and total_ch:
            initial_skeleton = outline_svc.to_bible_outline(novel_id, 1, total_ch)
        elif l1_done:
            initial_skeleton = outline_svc.to_bible_outline(novel_id, 1, l1_done)
        else:
            initial_skeleton = []
        world_plan = (
            novel_svc.world_plan_from_bible(novel) if resume and bible.get("world") else None
        )

        def on_l0_complete(wp: dict) -> None:
            novel_svc.apply_l0_plan(novel_id, wp, target_chapters)

        def on_l1_batch(batch: list, done_through: int) -> None:
            outline_svc.upsert_batch(novel_id, batch, detail_level="skeleton", locked=True)
            novel_row = novel_svc.get_novel(novel_id)
            meta = parse_bible(novel_row.bible_json).get("meta", {})
            total = int(meta.get("total_chapters") or 1)
            progress = min(85, 10 + int(75 * done_through / total))
            novel_svc.update_planning_state(
                novel_id,
                phase="l1_skeleton",
                l1_done_through=done_through,
                progress=progress,
            )

        def on_l2_batch(batch: list, done_through: int) -> None:
            outline_svc.upsert_batch(novel_id, batch, detail_level="detailed", locked=True)
            novel_svc.update_planning_state(
                novel_id,
                phase="l2_detail",
                l2_done_through=done_through,
                progress=min(95, 86 + done_through // 2),
            )

        def on_progress(p: int) -> None:
            novel_svc.update_status(novel_id, "planning", min(95, 5 + p))

        handlers = PlanCheckpointHandlers(
            resume_state=state,
            initial_skeleton=initial_skeleton,
            on_l0_complete=on_l0_complete,
            on_l1_batch=on_l1_batch,
            on_l2_batch=on_l2_batch,
            on_progress=on_progress,
        )

        try:
            if not resume:
                novel_svc.update_status(novel_id, "planning", 5)
            else:
                novel_svc.reset_for_planning(novel_id)

            plan = await plan_svc.execute_plan(
                novel.premise,
                novel.genre,
                target_chapters=target_chapters,
                world_plan=world_plan,
                handlers=handlers,
            )
            validate_plan(plan, target_chapters)
            l2_to = int(plan.get("meta", {}).get("l2_detail_to") or L2_INITIAL_WINDOW)
            novel_svc.finalize_planned(novel_id, l2_to)

        except Exception as exc:
            logger.exception("小说生成失败: %s", novel_id)
            novel_svc.set_planning_failed(novel_id, str(exc))
    finally:
        db.close()


async def run_novel_start_writing(novel_id: str, write_count: int = 3) -> None:
    db = SessionLocal()
    try:
        (
            novel_svc,
            plan_svc,
            write_svc,
            memory_svc,
            beat_svc,
            validate_svc,
            entity_svc,
            framework_svc,
            postwrite_svc,
            outline_svc,
        ) = _build_services(db)

        novel = novel_svc.get_novel(novel_id)
        if not novel:
            return
        # API 已 try_lock 时 status=writing；兼容 Celery/测试直接调用
        if novel.status == "planned":
            novel_svc.update_status(novel_id, "writing", 20)
        elif novel.status != "writing":
            return

        try:
            all_ok = await _write_initial_chapters(
                novel_id,
                novel_svc,
                write_svc,
                memory_svc,
                beat_svc,
                validate_svc,
                entity_svc,
                framework_svc,
                postwrite_svc,
                outline_svc,
                plan_svc,
                write_count,
            )
            if all_ok:
                novel_svc.finalize_after_writing_batch(novel_id)
        except Exception as exc:
            logger.exception("开始写作失败: %s", novel_id)
            novel_svc.set_failed(novel_id, str(exc))
    finally:
        db.close()


async def run_novel_next_chapter(novel_id: str, write_count: int = 1) -> None:
    db = SessionLocal()
    try:
        (
            novel_svc,
            plan_svc,
            write_svc,
            memory_svc,
            beat_svc,
            validate_svc,
            entity_svc,
            framework_svc,
            postwrite_svc,
            outline_svc,
        ) = _build_services(db)

        novel = novel_svc.get_novel(novel_id)
        if not novel:
            return
        if novel_svc.has_blocking_review(novel_id):
            novel_svc.set_review_required(novel_id, novel.progress)
            return

        next_index = novel_svc.next_chapter_index(novel_id)
        bible = parse_bible(novel.bible_json)
        if not outline_svc.get_chapter(novel_id, next_index) and not _outline_entry(
            bible, next_index
        ):
            novel_svc.set_failed(novel_id, f"大纲已无第 {next_index} 章可写")
            return

        try:
            novel_svc.update_status(novel_id, "writing", novel.progress)
            all_ok = await _write_chapter_range(
                novel_id,
                next_index,
                write_count,
                novel_svc,
                write_svc,
                memory_svc,
                beat_svc,
                validate_svc,
                entity_svc,
                framework_svc,
                postwrite_svc,
                outline_svc,
                plan_svc,
            )
            if all_ok:
                novel_svc.finalize_after_writing_batch(novel_id)
            else:
                return
        except Exception as exc:
            logger.exception("续写失败: %s", novel_id)
            novel_svc.set_failed(novel_id, str(exc))
    finally:
        db.close()


async def run_approve_chapter(novel_id: str, chapter_index: int) -> None:
    """用户放行待复核章节，补写记忆管线。"""
    db = SessionLocal()
    try:
        novel_svc = NovelService(db)
        postwrite_svc = NovelPostwriteService(db)

        chapter = novel_svc.get_chapter(novel_id, chapter_index)
        if not chapter or chapter.status != "needs_review":
            return

        novel_svc.save_chapter(
            chapter.id,
            chapter.title,
            chapter.content,
            chapter.summary,
            chapter.word_count,
            status="completed",
            validation_status="passed",
            validation_score=chapter.validation_score,
            validation_issues=chapter.validation_issues,
        )
        await postwrite_svc.finalize_chapter(
            novel_id, chapter_index, chapter.title, chapter.content, chapter.summary
        )

        novel_svc.clear_review_block_if_none(novel_id)
    finally:
        db.close()


async def run_rewrite_chapter(novel_id: str, chapter_index: int) -> None:
    """用户触发：按 validation_issues 重写待复核章节。"""
    db = SessionLocal()
    try:
        (
            novel_svc,
            plan_svc,
            write_svc,
            memory_svc,
            beat_svc,
            validate_svc,
            entity_svc,
            framework_svc,
            postwrite_svc,
            outline_svc,
        ) = _build_services(db)

        novel = novel_svc.get_novel(novel_id)
        chapter = novel_svc.get_chapter(novel_id, chapter_index)
        if not novel or not chapter or chapter.status != "needs_review":
            return

        try:
            bible = parse_bible(novel.bible_json)
            await _ensure_l2_for_range(
                novel_id,
                chapter_index,
                min(
                    chapter_index + L2_BATCH_SIZE - 1,
                    int(bible.get("meta", {}).get("total_chapters") or chapter_index),
                ),
                novel_svc,
                plan_svc,
                outline_svc,
                framework_svc,
            )
            bible = parse_bible(novel_svc.get_novel(novel_id).bible_json)
            outline = _resolve_outline(outline_svc, novel_id, chapter_index, bible)
            if not outline:
                raise ValueError(f"大纲中不存在第 {chapter_index} 章")

            title = outline.get("title", f"第{chapter_index}章")
            novel_svc.set_chapter_status(chapter.id, "writing")

            prev_tail = ""
            if chapter_index > 1:
                prev = novel_svc.get_chapter(novel_id, chapter_index - 1)
                if prev and prev.content:
                    prev_tail = prev.content

            fs_items = foreshadowing_for_chapter(bible, chapter_index)
            beats = get_beats_for_chapter(bible, chapter_index)
            if not beats:
                beats = await beat_svc.generate_beats(
                    novel.premise, novel.genre, bible, outline, fs_items
                )
                bible = save_beats_for_chapter(bible, chapter_index, beats)
                novel_svc.save_bible(novel_id, bible)

            query = f"第{chapter_index}章 {title} {outline.get('summary', '')}"
            snippets = memory_svc.query_relevant(novel_id, query)
            framework_snippets = framework_svc.query_hybrid(novel_id, query, chapter_index)
            entities_prompt = entity_svc.entities_to_prompt(entity_svc.list_confirmed(novel_id))
            plant_snippets = get_plant_snippets(novel_svc, novel_id, fs_items, chapter_index)
            bible_summary = bible_to_prompt_summary(bible)
            issues = json.loads(chapter.validation_issues or "[]")

            write_kw = dict(
                premise=novel.premise,
                genre=novel.genre,
                bible=bible,
                chapter_outline=outline,
                memory_snippets=snippets,
                prev_tail=prev_tail,
                beats=beats,
                foreshadowing=fs_items,
                entities_prompt=entities_prompt,
                framework_snippets=framework_snippets,
                plant_snippets=plant_snippets,
            )
            content, summary, word_count = await write_svc.rewrite_chapter(
                **write_kw,
                previous_content=chapter.content,
                issues=issues,
            )
            result = await validate_svc.validate_chapter(
                novel.genre,
                chapter_index,
                title,
                content,
                summary,
                word_count,
                outline,
                beats,
                fs_items,
                bible_summary,
            )
            issues_json = validate_svc.issues_to_json(result.issues)

            if result.passed:
                novel_svc.save_chapter(
                    chapter.id,
                    title,
                    content,
                    summary,
                    word_count,
                    status="completed",
                    validation_status="passed",
                    validation_score=result.score,
                    validation_issues=issues_json,
                )
                await postwrite_svc.finalize_chapter(
                    novel_id, chapter_index, title, content, summary
                )
                novel_svc.clear_review_block_if_none(novel_id)
                if not novel_svc.has_blocking_review(novel_id):
                    novel_svc.finalize_after_writing_batch(novel_id)
            else:
                novel_svc.save_chapter(
                    chapter.id,
                    title,
                    content,
                    summary,
                    word_count,
                    status="needs_review",
                    validation_status="needs_review",
                    validation_score=result.score,
                    validation_issues=issues_json,
                )
                novel_svc.set_review_required(novel_id, novel.progress)
        except Exception as exc:
            logger.exception("重写章节失败: %s 第%s章", novel_id, chapter_index)
            novel_svc.set_failed(novel_id, str(exc))
    finally:
        db.close()


async def run_replan_novel(novel_id: str) -> None:
    db = SessionLocal()
    try:
        novel_svc = NovelService(db)
        postwrite_svc = NovelPostwriteService(db)
        novel = novel_svc.get_novel(novel_id)
        if not novel:
            return
        last = max(
            (c.index for c in (novel.chapters or []) if c.status == "completed"),
            default=0,
        )
        if last == 0:
            return
        await postwrite_svc._maybe_replan(novel_id, last)
    finally:
        db.close()
