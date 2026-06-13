# @author zhangzhihao
"""DeepSeek / Zhipu Provider 请求体 mock 测试。"""

import pytest
import httpx

from app.core.config import Settings
from app.providers.base import Message
from app.providers.llm.deepseek import DeepSeekLLMProvider
from app.providers.llm.zhipu import ZhipuLLMProvider


@pytest.mark.asyncio
async def test_deepseek_chat_payload(monkeypatch):
    captured = {}

    class FakeResponse:
        status_code = 200

        def json(self):
            return {"choices": [{"message": {"content": "ok"}}]}

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def post(self, url, json=None, headers=None):
            captured["url"] = url
            captured["json"] = json
            captured["headers"] = headers
            return FakeResponse()

    monkeypatch.setattr(httpx, "AsyncClient", FakeClient)
    settings = Settings(
        deepseek_api_key="test-key",
        deepseek_api_base="https://api.deepseek.com",
        deepseek_model="deepseek-chat",
    )
    provider = DeepSeekLLMProvider(settings)
    result = await provider.chat([Message("user", "hello")], max_tokens=8192)
    assert result == "ok"
    assert captured["url"] == "https://api.deepseek.com/v1/chat/completions"
    assert captured["json"]["model"] == "deepseek-chat"
    assert captured["json"]["max_tokens"] == 8192
    assert captured["headers"]["Authorization"] == "Bearer test-key"


@pytest.mark.asyncio
async def test_zhipu_chat_payload(monkeypatch):
    captured = {}

    class FakeResponse:
        status_code = 200

        def json(self):
            return {"choices": [{"message": {"content": "glm"}}]}

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def post(self, url, json=None, headers=None):
            captured["url"] = url
            captured["json"] = json
            return FakeResponse()

    monkeypatch.setattr(httpx, "AsyncClient", FakeClient)
    settings = Settings(
        zhipu_api_key="zhipu-key",
        zhipu_api_base="https://open.bigmodel.cn/api/paas/v4",
        zhipu_model="glm-4-flash",
    )
    provider = ZhipuLLMProvider(settings)
    result = await provider.chat([Message("user", "hi")])
    assert result == "glm"
    assert captured["url"] == "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    assert captured["json"]["model"] == "glm-4-flash"
