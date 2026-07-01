# @author zhangzhihao
"""小说规划服务单元测试。"""

import pytest

from app.services.novel_plan_service import NovelPlanService


@pytest.mark.asyncio
async def test_generate_plan_mock():
    svc = NovelPlanService()
    plan = await svc.generate_plan("少年偶得仙缘", "xuanhuan", target_chapters=10)
    assert plan["title"]
    assert len(plan["outline"]) == 10
    assert plan["characters"]
    assert plan.get("volumes")
    assert plan.get("foreshadowing")
    assert plan.get("power_system")
    assert plan["outline"][0]["index"] == 1
    assert plan["outline"][-1]["index"] == 10
