# @author zhangzhihao
"""LangGraph 视频生成工作流骨架。"""

from typing import TypedDict

from langgraph.graph import END, StateGraph


class PipelineState(TypedDict, total=False):
    """Pipeline 全局状态。"""

    story: str
    script: dict
    assets: list
    keyframes: list
    video_clips: list
    audio: dict
    output_url: str
    current_step: str


async def script_node(state: PipelineState) -> PipelineState:
    """① 脚本 & 分镜（LLM）。"""
    # TODO: 调用 LLMProvider 生成分镜
    return {**state, "script": {"shots": []}, "current_step": "script"}


async def asset_node(state: PipelineState) -> PipelineState:
    """② 资产生成（角色/场景/道具图）。"""
    # TODO: 调用 ImageProvider
    return {**state, "assets": [], "current_step": "asset"}


async def keyframe_node(state: PipelineState) -> PipelineState:
    """③ 关键帧生成。"""
    # TODO: 调用 ImageProvider，注入资产上下文
    return {**state, "keyframes": [], "current_step": "keyframe"}


async def video_node(state: PipelineState) -> PipelineState:
    """④ 视频片段生成。"""
    # TODO: 调用 VideoProvider
    return {**state, "video_clips": [], "current_step": "video"}


async def tts_node(state: PipelineState) -> PipelineState:
    """⑤ 配音（TTS）。"""
    # TODO: 调用 TTSProvider
    return {**state, "audio": {}, "current_step": "tts"}


async def compose_node(state: PipelineState) -> PipelineState:
    """⑥ 合成成片（FFmpeg）。"""
    # TODO: 片段 + 配音 + 字幕 + BGM 合成
    return {**state, "output_url": "https://example.com/mock-output.mp4", "current_step": "compose"}


def build_video_pipeline():
    """构建 script → asset → keyframe → video → tts → compose 工作流。"""
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
