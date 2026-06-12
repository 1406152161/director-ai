# @author zhangzhihao
"""图像 Provider 占位实现。"""

from app.core.config import Settings, get_settings
from app.providers.base import ImageResult


class MockImageProvider:
    """返回 mock 图片 URL，供本地开发与测试。"""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    async def text_to_image(self, prompt: str, **kwargs: object) -> ImageResult:
        size = kwargs.get("size", "768x1344")
        return ImageResult(
            url=f"https://placehold.co/{size}/png?text=mock",
            prompt=prompt,
        )
