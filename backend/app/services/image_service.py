# @author zhangzhihao
"""分镜配图生成服务。"""

import asyncio
from collections.abc import Awaitable, Callable

from app.core.constants import aspect_to_size, style_to_prompt
from app.providers.base import ImageProvider
from app.providers.registry import get_image_provider
from app.services.script_service import ShotData

# 小并发防限流
_MAX_CONCURRENCY = 2


class ImageService:
    """为每个镜头生成配图。"""

    def __init__(self, image_provider: ImageProvider | None = None) -> None:
        self._image = image_provider or get_image_provider()

    def _build_prompt(self, shot: ShotData, style: str) -> str:
        style_words = style_to_prompt(style)
        return f"{shot.image_prompt_en}, {style_words}"

    async def generate_images(
        self,
        shots: list[ShotData],
        style: str,
        aspect_ratio: str,
        on_shot_done: Callable[[ShotData, str, int, int], Awaitable[None]] | None = None,
    ) -> list[str]:
        """逐镜头生成配图，返回 image_url 列表（与 shots 顺序一致）。"""
        size = aspect_to_size(aspect_ratio)
        semaphore = asyncio.Semaphore(_MAX_CONCURRENCY)
        results: list[str | None] = [None] * len(shots)
        completed = 0
        lock = asyncio.Lock()

        async def _generate_one(idx: int, shot: ShotData) -> None:
            nonlocal completed
            async with semaphore:
                prompt = self._build_prompt(shot, style)
                result = await self._image.text_to_image(prompt, size=size)
                results[idx] = result.url
                async with lock:
                    completed += 1
                    current = completed
                if on_shot_done:
                    await on_shot_done(shot, result.url, current, len(shots))

        await asyncio.gather(*[_generate_one(i, shot) for i, shot in enumerate(shots)])
        return [url for url in results if url is not None]
