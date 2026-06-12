# @author zhangzhihao
"""Agnes Provider 单元测试（mock httpx，不依赖网络）。"""


import httpx
import pytest
from app.core.config import Settings
from app.providers.base import Message
from app.providers.exceptions import (
    ProviderAuthError,
    ProviderBadRequestError,
    ProviderTimeoutError,
)
from app.providers.image.agnes import AgnesImageProvider
from app.providers.llm.agnes import AgnesLLMProvider


@pytest.fixture
def agnes_settings():
    return Settings(
        agnes_api_key="test-key",
        agnes_api_base="https://apihub.agnes-ai.com",
        agnes_llm_model="agnes-2.0-flash",
        agnes_image_model="agnes-image-2.1-flash",
    )


class TestAgnesLLMProvider:
    @pytest.mark.asyncio
    async def test_chat_request_body(self, agnes_settings, monkeypatch):
        captured: dict = {}

        class MockResponse:
            status_code = 200

            def json(self):
                return {"choices": [{"message": {"content": "hello"}}]}

        class MockClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

            async def post(self, url, json=None, headers=None):
                captured["url"] = url
                captured["json"] = json
                captured["headers"] = headers
                return MockResponse()

        monkeypatch.setattr(httpx, "AsyncClient", lambda **kw: MockClient())

        provider = AgnesLLMProvider(agnes_settings)
        result = await provider.chat(
            [Message(role="system", content="sys"), Message(role="user", content="hi")],
            enable_thinking=True,
            temperature=0.5,
            max_tokens=1024,
        )

        assert result == "hello"
        assert captured["url"] == "https://apihub.agnes-ai.com/v1/chat/completions"
        assert captured["json"]["model"] == "agnes-2.0-flash"
        assert captured["json"]["chat_template_kwargs"] == {"enable_thinking": True}
        assert "test-key" in captured["headers"]["Authorization"]
        assert "test-key" not in str(captured["json"])

    @pytest.mark.asyncio
    async def test_chat_401(self, agnes_settings, monkeypatch):
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

        provider = AgnesLLMProvider(agnes_settings)
        with pytest.raises(ProviderAuthError):
            await provider.chat([Message(role="user", content="hi")])

    @pytest.mark.asyncio
    async def test_chat_timeout(self, agnes_settings, monkeypatch):
        class MockClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

            async def post(self, *args, **kwargs):
                raise httpx.TimeoutException("timeout")

        monkeypatch.setattr(httpx, "AsyncClient", lambda **kw: MockClient())

        provider = AgnesLLMProvider(agnes_settings)
        with pytest.raises(ProviderTimeoutError):
            await provider.chat([Message(role="user", content="hi")])


class TestAgnesImageProvider:
    @pytest.mark.asyncio
    async def test_text_to_image_extra_body(self, agnes_settings, monkeypatch):
        captured: dict = {}

        class MockResponse:
            status_code = 200

            def json(self):
                return {"data": [{"url": "https://img.example/1.png"}]}

        class MockClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

            async def post(self, url, json=None, headers=None):
                captured["json"] = json
                return MockResponse()

        monkeypatch.setattr(httpx, "AsyncClient", lambda **kw: MockClient())

        provider = AgnesImageProvider(agnes_settings)
        result = await provider.text_to_image("a cat", size="768x1344")

        assert result.url == "https://img.example/1.png"
        assert captured["json"]["model"] == "agnes-image-2.1-flash"
        assert captured["json"]["prompt"] == "a cat"
        assert captured["json"]["size"] == "768x1344"
        # response_format 必须在 extra_body
        assert captured["json"]["extra_body"]["response_format"] == "url"
        assert "response_format" not in captured["json"]

    @pytest.mark.asyncio
    async def test_text_to_image_400(self, agnes_settings, monkeypatch):
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

        provider = AgnesImageProvider(agnes_settings)
        with pytest.raises(ProviderBadRequestError):
            await provider.text_to_image("prompt")
