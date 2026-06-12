# @author zhangzhihao
"""图像 Provider 占位实现。"""

from app.providers.base import ImageResult


class MockImageProvider:
    """返回 mock 图片 URL，M1 接入即梦 / 通义万相等。"""

    async def text_to_image(self, prompt: str, **kwargs: object) -> ImageResult:
        # TODO: 接入真实文生图 API
        return ImageResult(
            url="https://placehold.co/1024x576/png?text=mock-image",
            prompt=prompt,
        )
