# @author zhangzhihao
"""规划流水线 checkpoint 回调。"""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass
class PlanCheckpointHandlers:
    """可选回调：run_novel_generation 写入 DB；单测不传则内存完成。"""

    on_l0_complete: Callable[[dict[str, Any]], None] | None = None
    on_l1_batch: Callable[[list[dict], int], None] | None = None
    on_l2_batch: Callable[[list[dict], int], None] | None = None
    on_progress: Callable[[int], None] | None = None
    resume_state: dict[str, Any] = field(default_factory=dict)
    initial_skeleton: list[dict] = field(default_factory=list)


def planning_state_from_meta(meta: dict[str, Any]) -> dict[str, Any]:
    return dict(meta.get("planning_state") or {})


def can_resume_planning(meta: dict[str, Any]) -> bool:
    state = planning_state_from_meta(meta)
    if state.get("phase") in ("l1_skeleton", "l2_detail"):
        return True
    return int(state.get("l1_done_through") or 0) > 0 or bool(meta.get("world"))
