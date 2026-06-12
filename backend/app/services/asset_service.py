# @author zhangzhihao
"""导演设定资产生成服务。"""

import asyncio
import logging
from collections.abc import Awaitable, Callable

from app.core.constants import aspect_to_size
from app.providers.base import ImageProvider
from app.providers.registry import get_image_provider

logger = logging.getLogger(__name__)

_MAX_CONCURRENCY = 2


class AssetService:
    """为角色/场景/道具生成设定参考图。"""

    def __init__(self, image_provider: ImageProvider | None = None) -> None:
        self._image = image_provider or get_image_provider()

    async def generate_assets(
        self,
        assets: list[dict],
        aspect_ratio: str,
        on_done: Callable[[str, str, int, int], Awaitable[None]] | None = None,
    ) -> dict[str, str]:
        """逐资产文生图，返回 asset_key → image_url 映射。"""
        size = aspect_to_size(aspect_ratio)
        semaphore = asyncio.Semaphore(_MAX_CONCURRENCY)
        results: dict[str, str] = {}
        completed = 0
        lock = asyncio.Lock()
        total = len(assets)

        async def _generate_one(item: dict) -> None:
            nonlocal completed
            asset_key = item["asset_key"]
            prompt = item.get("description_en", "").strip() or item.get("name_cn", "")
            async with semaphore:
                result = await self._image.text_to_image(
                    f"{prompt}, character design sheet, consistent appearance, high detail",
                    size=size,
                )
                async with lock:
                    results[asset_key] = result.url
                    completed += 1
                    current = completed
                if on_done:
                    await on_done(asset_key, result.url, current, total)

        await asyncio.gather(*[_generate_one(a) for a in assets])
        return results
