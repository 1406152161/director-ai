# @author zhangzhihao
"""小说 LangGraph 轻量编排占位。"""

from app.services.novel_generation_service import run_novel_generation, run_novel_next_chapter


async def run_novel_pipeline(novel_id: str) -> None:
    """首版编排：规划 → 写前 N 章（委托 generation_service）。"""
    await run_novel_generation(novel_id)


async def run_next_chapter_pipeline(novel_id: str) -> None:
    """续写下一章编排入口。"""
    await run_novel_next_chapter(novel_id)
