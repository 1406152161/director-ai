# @author zhangzhihao
"""Agnes Image Provider — 文生图 generations API。"""

import logging

import httpx

from app.core.config import Settings, get_settings
from app.providers.base import ImageResult
from app.providers.exceptions import (
    ProviderAuthError,
    ProviderBadRequestError,
    ProviderError,
    ProviderTimeoutError,
)

logger = logging.getLogger(__name__)

_DEFAULT_TIMEOUT = 360.0


class AgnesImageProvider:
    """调用 Agnes 图像生成 API。"""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    @property
    def _api_base(self) -> str:
        return self._settings.agnes_api_base.rstrip("/")

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._settings.agnes_api_key}",
            "Content-Type": "application/json",
        }

    async def text_to_image(self, prompt: str, **kwargs: object) -> ImageResult:
        """文生图，返回图片 URL。"""
        size = kwargs.get("size", "768x1344")
        response_format = kwargs.get("response_format", "url")

        # response_format 必须放 extra_body，放顶层会 400
        payload: dict = {
            "model": kwargs.get("model", self._settings.agnes_image_model),
            "prompt": prompt,
            "size": size,
            "extra_body": {"response_format": response_format},
        }

        url = f"{self._api_base}/v1/images/generations"
        timeout = float(kwargs.get("timeout", _DEFAULT_TIMEOUT))

        logger.info("Agnes Image 请求 model=%s size=%s url=%s", payload["model"], size, url)

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(url, json=payload, headers=self._headers)
        except httpx.TimeoutException as exc:
            raise ProviderTimeoutError("Agnes Image 请求超时") from exc
        except httpx.HTTPError as exc:
            raise ProviderError(f"Agnes Image 网络错误: {exc}") from exc

        if response.status_code == 401:
            raise ProviderAuthError("Agnes Image 认证失败，请检查 API Key")
        if response.status_code == 400:
            raise ProviderBadRequestError(f"Agnes Image 请求参数错误: {response.text}")
        if response.status_code >= 400:
            raise ProviderError(
                f"Agnes Image 请求失败 ({response.status_code}): {response.text}"
            )

        data = response.json()
        try:
            image_url = data["data"][0]["url"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError(f"Agnes Image 响应格式异常: {data}") from exc

        return ImageResult(url=image_url, prompt=prompt)
