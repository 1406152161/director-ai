# @author zhangzhihao
"""智谱 LLM Provider — OpenAI 兼容 chat/completions。"""

import logging

import httpx

from app.core.config import Settings, get_settings
from app.providers.base import Message
from app.providers.exceptions import (
    ProviderAuthError,
    ProviderBadRequestError,
    ProviderError,
    ProviderTimeoutError,
)

logger = logging.getLogger(__name__)

_DEFAULT_TIMEOUT = 120.0


class ZhipuLLMProvider:
    """调用智谱 GLM 文本生成 API。"""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    @property
    def _api_base(self) -> str:
        return self._settings.zhipu_api_base.rstrip("/")

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._settings.zhipu_api_key}",
            "Content-Type": "application/json",
        }

    async def chat(self, messages: list[Message], **kwargs: object) -> str:
        """发送对话请求，返回 assistant 文本内容。"""
        payload: dict = {
            "model": kwargs.get("model", self._settings.zhipu_model),
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 8192),
        }

        url = f"{self._api_base}/chat/completions"
        timeout = float(kwargs.get("timeout", _DEFAULT_TIMEOUT))

        logger.info("Zhipu LLM 请求 model=%s url=%s", payload["model"], url)

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(url, json=payload, headers=self._headers)
        except httpx.TimeoutException as exc:
            raise ProviderTimeoutError("Zhipu LLM 请求超时") from exc
        except httpx.HTTPError as exc:
            raise ProviderError(f"Zhipu LLM 网络错误: {exc}") from exc

        if response.status_code == 401:
            raise ProviderAuthError("Zhipu LLM 认证失败，请检查 API Key")
        if response.status_code == 400:
            raise ProviderBadRequestError(f"Zhipu LLM 请求参数错误: {response.text}")
        if response.status_code >= 400:
            raise ProviderError(f"Zhipu LLM 请求失败 ({response.status_code}): {response.text}")

        data = response.json()
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError(f"Zhipu LLM 响应格式异常: {data}") from exc
