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
        self.i2i_calls = 0
        self.prompts: list[str] = []
        self.ref_urls: list[list[str]] = []

    async def text_to_image(self, prompt: str, **kwargs: object) -> ImageResult:
        self.calls += 1
        self.prompts.append(prompt)
        return ImageResult(url=f"https://mock/{self.calls}.png", prompt=prompt)

    async def image_to_image(
        self, prompt: str, reference_urls: list[str], **kwargs: object
    ) -> ImageResult:
        self.i2i_calls += 1
        self.prompts.append(prompt)
        self.ref_urls.append(reference_urls)
        return ImageResult(
            url=f"https://mock/i2i-{self.i2i_calls}.png", prompt=prompt
        )


@pytest.mark.asyncio
async def test_build_prompt_no_style_conflict():
    svc = ImageService(image_provider=CountingImageProvider())
    shot = ShotData(
        index=1,
        scene_cn="橘猫街头",
        image_prompt_en="anime style, orange tabby cat walking Tokyo street, neon lights",
        motion_prompt_en="slow tracking shot",
        narration_cn="旁白",
        duration=4,
    )
    prompt = svc._build_prompt(shot, "cinematic")

    assert "anime style" in prompt
    assert "orange tabby cat" in prompt
    assert "cinematic realism" not in prompt
    assert "film still" not in prompt
    assert prompt.endswith("high detail")


@pytest.mark.asyncio
async def test_generate_images_for_shots():
    provider = CountingImageProvider()
    svc = ImageService(image_provider=provider)

    shots = [
        ShotData(1, "场景1", "anime style, prompt one", "slow pan", "旁白1", 4),
        ShotData(2, "场景2", "anime style, prompt two", "tracking shot", "旁白2", 4),
    ]

    progress_log: list[tuple[int, int]] = []

    async def on_shot_done(shot, url: str, done: int, total: int) -> None:
        progress_log.append((done, total))

    urls = await svc.generate_images(shots, "cinematic", "9:16", on_shot_done=on_shot_done)

    assert len(urls) == 2
    assert provider.calls == 2
    assert all("mock" in url for url in urls)
    assert progress_log[-1] == (2, 2)
    for sent_prompt in provider.prompts:
        assert "anime style" in sent_prompt
        assert "cinematic realism" not in sent_prompt
        assert "film still" not in sent_prompt


@pytest.mark.asyncio
async def test_generate_keyframes_uses_image_to_image():
    from app.services.script_service import AssetsData, CharacterAssetData, SceneAssetData, ShotData

    provider = CountingImageProvider()
    svc = ImageService(image_provider=provider)

    assets = AssetsData(
        characters=[
            CharacterAssetData("char_main", "橘猫", "orange tabby cat, anime style")
        ],
        scenes=[SceneAssetData("scene_main", "东京", "Tokyo street at dusk")],
    )
    url_map = {"char_main": "https://asset/char.png", "scene_main": "https://asset/scene.png"}
    shots = [
        ShotData(
            1, "场景1", "anime cat prompt", "slow pan", "旁白1", 4,
            character_ids=["char_main"], scene_id="scene_main",
        ),
    ]

    urls = await svc.generate_keyframes(shots, assets, url_map, "anime", "9:16")

    assert len(urls) == 1
    assert provider.i2i_calls == 1
    assert len(provider.ref_urls[0]) == 2
    assert "i2i" in urls[0]
