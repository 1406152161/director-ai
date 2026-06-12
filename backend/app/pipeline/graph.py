# @author zhangzhihao
"""LangGraph 视频生成工作流。"""

from typing import TypedDict

from langgraph.graph import END, StateGraph

from app.services.image_service import ImageService
from app.services.script_service import ScriptService


class PipelineState(TypedDict, total=False):
    """Pipeline 全局状态。"""

    story: str
    style: str
    duration: int
    aspect_ratio: str
    script: dict
    image_urls: list
    assets: list
    keyframes: list
    video_clips: list
    audio: dict
    output_url: str
    current_step: str


async def script_node(state: PipelineState) -> PipelineState:
    """① 脚本 & 分镜（LLM）。"""
    svc = ScriptService()
    result = await svc.generate_script(
        state.get("story", ""),
        state.get("style", "cinematic"),
        state.get("duration", 30),
    )
    script = {
        "title": result.title,
        "shots": [
            {
                "index": s.index,
                "scene_cn": s.scene_cn,
                "image_prompt_en": s.image_prompt_en,
                "motion_prompt_en": s.motion_prompt_en,
                "narration_cn": s.narration_cn,
                "duration": s.duration,
            }
            for s in result.shots
        ],
    }
    return {**state, "script": script, "current_step": "script"}


async def image_node(state: PipelineState) -> PipelineState:
    """② 逐镜头配图（M1 核心节点）。"""
    from app.services.script_service import ShotData

    script = state.get("script", {})
    shots_raw = script.get("shots", [])
    shots = [
        ShotData(
            index=item["index"],
            scene_cn=item.get("scene_cn", ""),
            image_prompt_en=item.get("image_prompt_en", ""),
            motion_prompt_en=item.get("motion_prompt_en", ""),
            narration_cn=item.get("narration_cn", ""),
            duration=item.get("duration", 4),
        )
        for item in shots_raw
    ]

    svc = ImageService()
    urls = await svc.generate_images(
        shots,
        state.get("style", "cinematic"),
        state.get("aspect_ratio", "9:16"),
    )
    return {**state, "image_urls": urls, "current_step": "image"}


async def asset_node(state: PipelineState) -> PipelineState:
    """资产生成（角色/场景/道具图）— M1 占位。"""
    return {**state, "assets": [], "current_step": "asset"}


async def keyframe_node(state: PipelineState) -> PipelineState:
    """关键帧生成 — M1 占位。"""
    return {**state, "keyframes": [], "current_step": "keyframe"}


async def video_node(state: PipelineState) -> PipelineState:
    """视频片段生成 — M1 占位。"""
    return {**state, "video_clips": [], "current_step": "video"}


async def tts_node(state: PipelineState) -> PipelineState:
    """配音（TTS）— M1 占位。"""
    return {**state, "audio": {}, "current_step": "tts"}


async def compose_node(state: PipelineState) -> PipelineState:
    """合成成片（FFmpeg）— M1 占位。"""
    return {
        **state,
        "output_url": "https://example.com/mock-output.mp4",
        "current_step": "compose",
    }


def build_m1_pipeline():
    """M1 精简工作流：script → image → END。"""
    graph = StateGraph(PipelineState)
    graph.add_node("script", script_node)
    graph.add_node("image", image_node)
    graph.set_entry_point("script")
    graph.add_edge("script", "image")
    graph.add_edge("image", END)
    return graph.compile()


def build_video_pipeline():
    """完整工作流：script → asset → keyframe → video → tts → compose。"""
    graph = StateGraph(PipelineState)

    graph.add_node("script", script_node)
    graph.add_node("asset", asset_node)
    graph.add_node("keyframe", keyframe_node)
    graph.add_node("video", video_node)
    graph.add_node("tts", tts_node)
    graph.add_node("compose", compose_node)

    graph.set_entry_point("script")
    graph.add_edge("script", "asset")
    graph.add_edge("asset", "keyframe")
    graph.add_edge("keyframe", "video")
    graph.add_edge("video", "tts")
    graph.add_edge("tts", "compose")
    graph.add_edge("compose", END)

    return graph.compile()
