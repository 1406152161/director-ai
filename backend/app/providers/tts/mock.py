# @author zhangzhihao
"""TTS Provider 占位实现。"""

from app.core.config import Settings, get_settings
from app.providers.base import TTSResult


class MockTTSProvider:
    """返回 mock 音频 URL，M1 接入 Edge-TTS / 阿里云等。"""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    async def synthesize(self, text: str, **kwargs: object) -> TTSResult:
        # TODO: 接入真实 TTS API
        return TTSResult(
            audio_url="https://example.com/mock-audio.mp3",
            duration=len(text) * 0.15,
        )
