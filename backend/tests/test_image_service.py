# @author zhangzhihao
"""配图服务测试。"""

import pytest
from app.providers.base import ImageResult
from app.services.image_service import ImageService
from app.services.script_service import ShotData


class CountingImageProvider:
    """记录调用次数的 mock image provider。"""

    def __init__(self):
        self.calls = 0

    async def text_to_image(self, prompt: str, **kwargs: object) -> ImageResult:
        self.calls += 1
        return ImageResult(url=f"https://mock/{self.calls}.png", prompt=prompt)


@pytest.mark.asyncio
async def test_generate_images_for_shots():
    provider = CountingImageProvider()
    svc = ImageService(image_provider=provider)

    shots = [
        ShotData(1, "场景1", "prompt one", "旁白1", 4),
        ShotData(2, "场景2", "prompt two", "旁白2", 4),
    ]

    progress_log: list[tuple[int, int]] = []

    async def on_shot_done(shot, url: str, done: int, total: int) -> None:
        progress_log.append((done, total))

    urls = await svc.generate_images(shots, "cinematic", "9:16", on_shot_done=on_shot_done)

    assert len(urls) == 2
    assert provider.calls == 2
    assert all("mock" in url for url in urls)
    assert progress_log[-1] == (2, 2)
