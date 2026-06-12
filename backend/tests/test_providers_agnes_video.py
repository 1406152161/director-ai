# @author zhangzhihao
"""Agnes Video Provider 单元测试（mock httpx）。"""

import asyncio

import httpx
import pytest
from app.core.config import Settings
from app.core.constants import duration_to_num_frames
from app.providers.exceptions import (
    ProviderAuthError,
    ProviderBadRequestError,
    ProviderError,
    ProviderTimeoutError,
)
from app.providers.video.agnes import AgnesVideoProvider


@pytest.fixture
def video_settings():
    return Settings(
        agnes_api_key="test-key",
        agnes_api_base="https://apihub.agnes-ai.com",
        agnes_video_model="agnes-video-v2.0",
        agnes_video_frame_rate=24,
        agnes_video_max_frames=441,
        agnes_video_poll_interval=0.01,
        agnes_video_timeout=1.0,
    )


class TestDurationToNumFrames:
    def test_valid_8n_plus_1_values(self):
        assert duration_to_num_frames(3, frame_rate=24) == 81
        assert duration_to_num_frames(5, frame_rate=24) == 121
        assert duration_to_num_frames(7, frame_rate=24) == 161
        assert duration_to_num_frames(10, frame_rate=24) == 241
        assert duration_to_num_frames(18, frame_rate=24) == 441

    def test_clamps_to_max_frames(self):
        assert duration_to_num_frames(100, frame_rate=24, max_frames=441) == 441


class TestAgnesVideoProvider:
    @pytest.mark.asyncio
    async def test_create_request_body(self, video_settings, monkeypatch):
        captured: dict = {}
        poll_count = 0

        class MockResponse:
            def __init__(self, status_code, data=None, text=""):
                self.status_code = status_code
                self._data = data or {}
                self.text = text

            def json(self):
                return self._data

        class MockClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

            async def post(self, url, json=None, headers=None):
                captured["create_url"] = url
                captured["create_json"] = json
                captured["headers"] = headers
                return MockResponse(200, {
                    "id": "task_abc123",
                    "task_id": "task_abc123",
                    "video_id": "video_xyz789",
                })

            async def get(self, url, params=None, headers=None):
                nonlocal poll_count
                poll_count += 1
                captured["poll_params"] = params
                if poll_count == 1:
                    return MockResponse(200, {"status": "in_progress"})
                return MockResponse(
                    200,
                    {
                        "status": "completed",
                        "remixed_from_video_id": "https://cdn.example/final.mp4",
                    },
                )

        monkeypatch.setattr(httpx, "AsyncClient", lambda **kw: MockClient())

        async def noop_sleep(_):
            pass

        monkeypatch.setattr(asyncio, "sleep", noop_sleep)

        provider = AgnesVideoProvider(video_settings)
        result = await provider.image_to_video(
            "https://img.example/1.png",
            "slow pan shot",
            duration=5,
            aspect_ratio="9:16",
        )

        assert result.url == "https://cdn.example/final.mp4"
        assert captured["create_url"] == "https://apihub.agnes-ai.com/v1/videos"
        body = captured["create_json"]
        assert body["model"] == "agnes-video-v2.0"
        assert body["prompt"] == "slow pan shot"
        assert body["image"] == "https://img.example/1.png"
        assert body["num_frames"] == 121
        assert body["frame_rate"] == 24
        assert body["width"] == 768
        assert body["height"] == 1344
        assert captured["poll_params"]["video_id"] == "video_xyz789"

    @pytest.mark.asyncio
    async def test_poll_failed_status(self, video_settings, monkeypatch):
        class MockResponse:
            status_code = 200

            def json(self):
                return {"status": "failed", "error": "generation error"}

        class CreateResponse:
            status_code = 200

            def json(self):
                return {"id": "v1"}

        class MockClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

            async def post(self, *args, **kwargs):
                return CreateResponse()

            async def get(self, *args, **kwargs):
                return MockResponse()

        monkeypatch.setattr(httpx, "AsyncClient", lambda **kw: MockClient())

        provider = AgnesVideoProvider(video_settings)
        with pytest.raises(ProviderError, match="生成失败"):
            await provider.image_to_video("https://img/1.png", "prompt", 5)

    @pytest.mark.asyncio
    async def test_create_401(self, video_settings, monkeypatch):
        class MockResponse:
            status_code = 401
            text = "Unauthorized"

        class MockClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

            async def post(self, *args, **kwargs):
                return MockResponse()

        monkeypatch.setattr(httpx, "AsyncClient", lambda **kw: MockClient())

        provider = AgnesVideoProvider(video_settings)
        with pytest.raises(ProviderAuthError):
            await provider.image_to_video("https://img/1.png", "prompt", 5)

    @pytest.mark.asyncio
    async def test_create_400(self, video_settings, monkeypatch):
        class MockResponse:
            status_code = 400
            text = "bad request"

        class MockClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

            async def post(self, *args, **kwargs):
                return MockResponse()

        monkeypatch.setattr(httpx, "AsyncClient", lambda **kw: MockClient())

        provider = AgnesVideoProvider(video_settings)
        with pytest.raises(ProviderBadRequestError):
            await provider.image_to_video("https://img/1.png", "prompt", 5)

    @pytest.mark.asyncio
    async def test_poll_timeout(self, video_settings, monkeypatch):
        class MockResponse:
            status_code = 200

            def json(self):
                return {"status": "queued"}

        class CreateResponse:
            status_code = 200

            def json(self):
                return {"id": "v1"}

        class MockClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

            async def post(self, *args, **kwargs):
                return CreateResponse()

            async def get(self, *args, **kwargs):
                return MockResponse()

        monkeypatch.setattr(httpx, "AsyncClient", lambda **kw: MockClient())

        async def noop_sleep(_):
            pass

        monkeypatch.setattr(asyncio, "sleep", noop_sleep)

        provider = AgnesVideoProvider(video_settings)
        with pytest.raises(ProviderTimeoutError):
            await provider.image_to_video("https://img/1.png", "prompt", 5)
