# @author zhangzhihao
"""小说规划服务单元测试。"""

import pytest

from app.services.novel_plan_service import NovelPlanService


@pytest.mark.asyncio
async def test_generate_plan_mock():
    svc = NovelPlanService()
    plan = await svc.generate_plan("少年偶得仙缘", "xuanhuan")
    assert plan["title"]
    assert len(plan["outline"]) >= 8
    assert plan["characters"]
