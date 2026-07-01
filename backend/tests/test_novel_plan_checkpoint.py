# @author zhangzhihao
"""规划 checkpoint 断点续跑测试。"""

import pytest
from app.novel.plan_checkpoint import (
    PlanCheckpointHandlers,
    can_resume_planning,
    planning_state_from_meta,
)
from app.services.novel_plan_service import NovelPlanService


def test_planning_state_helpers():
    meta = {
        "planning_state": {
            "phase": "l1_skeleton",
            "l1_done_through": 25,
            "l2_done_through": 0,
        }
    }
    state = planning_state_from_meta(meta)
    assert state["phase"] == "l1_skeleton"
    assert state["l1_done_through"] == 25
    assert can_resume_planning(meta) is True
    assert can_resume_planning({}) is False


@pytest.mark.asyncio
async def test_l1_checkpoint_resume_after_failure():
    svc = NovelPlanService()
    world_plan: dict | None = None
    skeleton_store: list[dict] = []

    def on_l0(wp: dict) -> None:
        nonlocal world_plan
        world_plan = wp

    def on_l1_fail(batch: list, done: int) -> None:
        skeleton_store.extend(batch)
        if done == 25:
            raise RuntimeError("simulated fail after batch 1")

    handlers = PlanCheckpointHandlers(on_l0_complete=on_l0, on_l1_batch=on_l1_fail)
    with pytest.raises(RuntimeError, match="simulated fail"):
        await svc.execute_plan(
            "少年偶得仙缘",
            "xuanhuan",
            target_chapters=50,
            handlers=handlers,
        )

    assert world_plan is not None
    assert len(skeleton_store) == 25

    resume_handlers = PlanCheckpointHandlers(
        resume_state={
            "phase": "l1_skeleton",
            "l1_done_through": 25,
            "l2_done_through": 0,
        },
        initial_skeleton=list(skeleton_store),
        on_l1_batch=lambda batch, done: skeleton_store.extend(batch),
    )
    plan = await svc.execute_plan(
        "少年偶得仙缘",
        "xuanhuan",
        target_chapters=50,
        world_plan=world_plan,
        handlers=resume_handlers,
    )
    assert len(plan["outline"]) == 50
    assert plan["outline"][0]["index"] == 1
    assert plan["outline"][-1]["index"] == 50
    assert len(skeleton_store) == 50
