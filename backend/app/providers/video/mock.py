# @author zhangzhihao
"""视频 Provider 占位实现。"""

from app.providers.base import VideoResult


class MockVideoProvider:
    """返回 mock 视频 URL，M1 接入可灵 / 即梦等。"""

    async def image_to_video(
        self, image_url: str, prompt: str, duration: int, **kwargs: object
    ) -> VideoResult:
        # TODO: 接入真实图生视频 API
        return VideoResult(
            url="https://example.com/mock-video.mp4",
            duration=duration,
        )
