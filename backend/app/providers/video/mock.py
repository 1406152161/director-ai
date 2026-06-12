# @author zhangzhihao
"""视频 Provider 占位实现。"""

from app.core.config import Settings, get_settings
from app.providers.base import VideoResult


class MockVideoProvider:
    """返回 mock 视频 URL，M1 接入可灵 / 即梦等。"""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    async def image_to_video(
        self, image_url: str, prompt: str, duration: int, **kwargs: object
    ) -> VideoResult:
        # TODO: 接入真实图生视频 API
        return VideoResult(
            url="https://example.com/mock-video.mp4",
            duration=duration,
        )
