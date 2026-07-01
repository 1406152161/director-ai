# @author zhangzhihao
"""规划 JSON 校验单元测试。"""

import pytest

from app.novel.plan_validate import validate_plan


def test_validate_plan_ok():
    plan = {
        "meta": {"total_chapters": 8},
        "outline": [{"index": i, "title": f"第{i}章", "summary": "x"} for i in range(1, 9)],
        "foreshadowing": [
            {"id": "fs1", "plant_chapter": 2, "resolve_chapter": 7},
        ],
    }
    validate_plan(plan)


def test_validate_plan_too_few_chapters():
    plan = {"outline": [{"index": 1, "title": "a", "summary": "b"}]}
    with pytest.raises(ValueError, match="不足"):
        validate_plan(plan)


def test_validate_plan_flex_range():
    plan = {"meta": {"total_chapters": 950}, "outline": []}
    validate_plan(plan, user_target=1000)

    with pytest.raises(ValueError, match="±200"):
        validate_plan({"meta": {"total_chapters": 700}, "outline": []}, user_target=1000)


def test_validate_plan_foreshadow_out_of_range():
    plan = {
        "meta": {"total_chapters": 8},
        "outline": [{"index": i, "title": "t", "summary": "s"} for i in range(1, 9)],
        "foreshadowing": [{"id": "fs1", "plant_chapter": 2, "resolve_chapter": 20}],
    }
    with pytest.raises(ValueError, match="回收章"):
        validate_plan(plan)
