# @author zhangzhihao
"""资产生成服务测试。"""

import pytest
from app.services.asset_service import AssetService


@pytest.mark.asyncio
async def test_generate_assets_continues_when_one_fails():
    calls: list[str] = []

    class FlakyImageProvider:
        async def text_to_image(self, prompt, size=None, **kwargs):
            if "bad" in prompt:
                raise RuntimeError("mock image failure")
            calls.append(prompt)
            from app.providers.base import ImageResult

            return ImageResult(url=f"https://example.com/{len(calls)}.png", prompt=prompt)

    svc = AssetService(image_provider=FlakyImageProvider())
    assets = [
        {"asset_key": "hero", "name_cn": "主角", "description_en": "hero"},
        {"asset_key": "villain", "name_cn": "反派", "description_en": "bad guy"},
    ]
    results = await svc.generate_assets(assets, "9:16")
    assert "hero" in results
    assert "villain" not in results
    assert len(calls) == 1
