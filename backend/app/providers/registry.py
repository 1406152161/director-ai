# @author zhangzhihao
"""Provider 工厂 / 注册表，按配置选择实现。"""

from app.core.config import Settings, get_settings
from app.providers.base import ImageProvider, LLMProvider, TTSProvider, VideoProvider
from app.providers.image.agnes import AgnesImageProvider
from app.providers.image.mock import MockImageProvider
from app.providers.llm.agnes import AgnesLLMProvider
from app.providers.llm.mock import MockLLMProvider
from app.providers.tts.mock import MockTTSProvider
from app.providers.video.mock import MockVideoProvider

_LLM_REGISTRY: dict[str, type] = {
    "mock": MockLLMProvider,
    "agnes": AgnesLLMProvider,
}

_IMAGE_REGISTRY: dict[str, type] = {
    "mock": MockImageProvider,
    "agnes": AgnesImageProvider,
}

_VIDEO_REGISTRY: dict[str, type] = {
    "mock": MockVideoProvider,
}

_TTS_REGISTRY: dict[str, type] = {
    "mock": MockTTSProvider,
}


def _resolve(registry: dict[str, type], name: str, kind: str, settings: Settings):
    if name not in registry:
        raise ValueError(f"未注册的 {kind} provider: {name}")
    return registry[name](settings)


def clear_provider_cache() -> None:
    """清除 provider 缓存，供测试切换配置（M1 无缓存，保留接口兼容）。"""


def get_llm_provider(settings: Settings | None = None) -> LLMProvider:
    cfg = settings or get_settings()
    return _resolve(_LLM_REGISTRY, cfg.llm_provider, "LLM", cfg)


def get_image_provider(settings: Settings | None = None) -> ImageProvider:
    cfg = settings or get_settings()
    return _resolve(_IMAGE_REGISTRY, cfg.image_provider, "Image", cfg)


def get_video_provider(settings: Settings | None = None) -> VideoProvider:
    cfg = settings or get_settings()
    return _resolve(_VIDEO_REGISTRY, cfg.video_provider, "Video", cfg)


def get_tts_provider(settings: Settings | None = None) -> TTSProvider:
    cfg = settings or get_settings()
    return _resolve(_TTS_REGISTRY, cfg.tts_provider, "TTS", cfg)
