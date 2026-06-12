# @author zhangzhihao
"""分镜配图生成服务。"""

import asyncio
from collections.abc import Awaitable, Callable

from app.core.constants import aspect_to_size
from app.providers.base import ImageProvider
from app.providers.registry import get_image_provider
from app.services.script_service import AssetsData, ShotData

_MAX_CONCURRENCY = 2


class ImageService:
    """为每个镜头生成配图。"""

    def __init__(self, image_provider: ImageProvider | None = None) -> None:
        self._image = image_provider or get_image_provider()

    def _build_prompt(self, shot: ShotData, _style: str) -> str:
        prompt = shot.image_prompt_en.strip()
        if not prompt:
            return "high detail"
        return f"{prompt}, high detail"

    def _build_keyframe_prompt(
        self, shot: ShotData, assets: AssetsData, style: str
    ) -> str:
        """关键帧提示词 = 镜头 prompt + 关联资产外观摘要。"""
        parts = [self._build_prompt(shot, style)]
        asset_map = {a.id: a.description_en for a in assets.characters}
        asset_map.update({a.id: a.description_en for a in assets.scenes})
        asset_map.update({a.id: a.description_en for a in assets.props})

        for cid in shot.character_ids:
            if cid in asset_map:
                parts.append(f"character reference: {asset_map[cid]}")
        if shot.scene_id and shot.scene_id in asset_map:
            parts.append(f"scene reference: {asset_map[shot.scene_id]}")
        for pid in shot.prop_ids:
            if pid in asset_map:
                parts.append(f"prop reference: {asset_map[pid]}")
        return ", ".join(parts)

    def _collect_reference_urls(
        self,
        shot: ShotData,
        url_map: dict[str, str],
    ) -> list[str]:
        """收集本镜引用的资产设定图 URL。"""
        refs: list[str] = []
        for cid in shot.character_ids:
            if cid in url_map and url_map[cid]:
                refs.append(url_map[cid])
        if shot.scene_id and shot.scene_id in url_map and url_map[shot.scene_id]:
            refs.append(url_map[shot.scene_id])
        for pid in shot.prop_ids:
            if pid in url_map and url_map[pid]:
                refs.append(url_map[pid])
        return refs

    async def generate_images(
        self,
        shots: list[ShotData],
        style: str,
        aspect_ratio: str,
        on_shot_done: Callable[[ShotData, str, int, int], Awaitable[None]] | None = None,
    ) -> list[str]:
        """逐镜头文生图（M2 路径）。"""
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

    async def generate_keyframes(
        self,
        shots: list[ShotData],
        assets: AssetsData,
        url_map: dict[str, str],
        style: str,
        aspect_ratio: str,
        on_shot_done: Callable[[ShotData, str, int, int], Awaitable[None]] | None = None,
    ) -> list[str]:
        """M3 关键帧：图生图，参考资产设定图。"""
        size = aspect_to_size(aspect_ratio)
        semaphore = asyncio.Semaphore(_MAX_CONCURRENCY)
        results: list[str | None] = [None] * len(shots)
        completed = 0
        lock = asyncio.Lock()

        async def _generate_one(idx: int, shot: ShotData) -> None:
            nonlocal completed
            async with semaphore:
                prompt = self._build_keyframe_prompt(shot, assets, style)
                refs = self._collect_reference_urls(shot, url_map)
                if refs:
                    result = await self._image.image_to_image(prompt, refs, size=size)
                else:
                    result = await self._image.text_to_image(prompt, size=size)
                results[idx] = result.url
                async with lock:
                    completed += 1
                    current = completed
                if on_shot_done:
                    await on_shot_done(shot, result.url, current, len(shots))

        await asyncio.gather(*[_generate_one(i, shot) for i, shot in enumerate(shots)])
        return [url for url in results if url is not None]
