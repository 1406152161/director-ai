# @author zhangzhihao
"""Provider 适配层 — 统一 AI 能力接口。"""

from app.providers.base import (
    ImageProvider,
    ImageResult,
    LLMProvider,
    Message,
    TTSProvider,
    TTSResult,
    VideoProvider,
    VideoResult,
)
from app.providers.registry import (
    get_image_provider,
    get_llm_provider,
    get_tts_provider,
    get_video_provider,
)

__all__ = [
    "ImageProvider",
    "ImageResult",
    "LLMProvider",
    "Message",
    "TTSProvider",
    "TTSResult",
    "VideoProvider",
    "VideoResult",
    "get_image_provider",
    "get_llm_provider",
    "get_tts_provider",
    "get_video_provider",
]
