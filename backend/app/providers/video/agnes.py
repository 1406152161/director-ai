# @author zhangzhihao
"""Agnes Video Provider — 图生视频创建与轮询。"""

import asyncio
import logging

import httpx

from app.core.config import Settings, get_settings
from app.core.constants import aspect_to_video_size, duration_to_num_frames
from app.providers.base import VideoResult
from app.providers.exceptions import (
    ProviderAuthError,
    ProviderBadRequestError,
    ProviderError,
    ProviderTimeoutError,
)

logger = logging.getLogger(__name__)

# 创建请求最多重试 3 次（共 4 次尝试），退避 2s / 4s / 8s
_CREATE_MAX_ATTEMPTS = 4
_CREATE_BACKOFF_BASE = 2.0


class AgnesVideoProvider:
    """调用 Agnes 图生视频 API：创建任务 + 轮询成片 URL。"""

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

    async def _create_video(
        self,
        image_url: str,
        prompt: str,
        num_frames: int,
        frame_rate: int,
        width: int,
        height: int,
    ) -> str:
        """创建视频任务，返回 video_id（单次请求，不含重试）。"""
        payload = {
            "model": self._settings.agnes_video_model,
            "prompt": prompt,
            "image": image_url,
            "num_frames": num_frames,
            "frame_rate": frame_rate,
            "width": width,
            "height": height,
        }
        url = f"{self._api_base}/v1/videos"
        logger.info(
            "Agnes Video 创建 model=%s frames=%d rate=%d",
            payload["model"],
            num_frames,
            frame_rate,
        )

        timeout = self._settings.agnes_video_create_timeout
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(url, json=payload, headers=self._headers)
        except httpx.TimeoutException as exc:
            raise ProviderTimeoutError("Agnes Video 创建请求超时") from exc
        except httpx.HTTPError as exc:
            raise ProviderError(f"Agnes Video 网络错误: {exc}") from exc

        if response.status_code == 401:
            raise ProviderAuthError("Agnes Video 认证失败，请检查 API Key")
        if response.status_code == 400:
            raise ProviderBadRequestError(f"Agnes Video 请求参数错误: {response.text}")
        if response.status_code >= 400:
            raise ProviderError(
                f"Agnes Video 创建失败 ({response.status_code}): {response.text}"
            )

        data = response.json()
        # 轮询端点需要 video_id，创建响应中 id 常为 task_id
        video_id = data.get("video_id") or data.get("id") or data.get("task_id")
        if not video_id:
            raise ProviderError(f"Agnes Video 响应缺少 video_id: {data}")
        return str(video_id)

    def _is_create_retryable(self, exc: Exception) -> bool:
        """创建阶段可重试：超时或 httpx 网络类 ProviderError。"""
        if isinstance(exc, ProviderTimeoutError):
            return True
        return isinstance(exc, ProviderError) and "网络错误" in str(exc)

    async def _create_video_with_retry(
        self,
        image_url: str,
        prompt: str,
        num_frames: int,
        frame_rate: int,
        width: int,
        height: int,
    ) -> str:
        """创建视频任务，遇超时/网络错误时指数退避重试。"""
        last_exc: Exception | None = None
        for attempt in range(_CREATE_MAX_ATTEMPTS):
            try:
                return await self._create_video(
                    image_url, prompt, num_frames, frame_rate, width, height
                )
            except (ProviderAuthError, ProviderBadRequestError):
                raise
            except Exception as exc:
                if not self._is_create_retryable(exc):
                    raise
                last_exc = exc
                if attempt == _CREATE_MAX_ATTEMPTS - 1:
                    break
                delay = _CREATE_BACKOFF_BASE ** (attempt + 1)
                logger.warning(
                    "Agnes Video 创建第 %d 次失败，%ss 后重试: %s",
                    attempt + 1,
                    delay,
                    exc,
                )
                await asyncio.sleep(delay)

        assert last_exc is not None
        raise last_exc

    async def _poll_video(self, video_id: str) -> str:
        """轮询直到 completed，返回 remixed_from_video_id（成片 URL）。"""
        poll_url = f"{self._api_base}/agnesapi"
        interval = self._settings.agnes_video_poll_interval
        timeout = self._settings.agnes_video_timeout
        elapsed = 0.0

        while elapsed < timeout:
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(
                        poll_url,
                        params={"video_id": video_id},
                        headers=self._headers,
                    )
            except httpx.TimeoutException as exc:
                raise ProviderTimeoutError("Agnes Video 轮询超时") from exc
            except httpx.HTTPError as exc:
                raise ProviderError(f"Agnes Video 轮询网络错误: {exc}") from exc

            if response.status_code == 401:
                raise ProviderAuthError("Agnes Video 认证失败，请检查 API Key")
            if response.status_code == 400:
                raise ProviderBadRequestError(f"Agnes Video 轮询参数错误: {response.text}")
            if response.status_code >= 400:
                raise ProviderError(
                    f"Agnes Video 轮询失败 ({response.status_code}): {response.text}"
                )

            data = response.json()
            status = data.get("status", "")
            logger.debug("Agnes Video 轮询 video_id=%s status=%s", video_id, status)

            if status == "completed":
                video_url = data.get("remixed_from_video_id")
                if not video_url:
                    raise ProviderError(
                        f"Agnes Video 已完成但缺少 remixed_from_video_id: {data}"
                    )
                return str(video_url)

            if status == "failed":
                error_msg = data.get("error") or data.get("message") or "未知错误"
                raise ProviderError(f"Agnes Video 生成失败: {error_msg}")

            await asyncio.sleep(interval)
            elapsed += interval

        raise ProviderTimeoutError(
            f"Agnes Video 轮询超时（{timeout}s），video_id={video_id}"
        )

    async def image_to_video(
        self, image_url: str, prompt: str, duration: int, **kwargs: object
    ) -> VideoResult:
        """图生视频：创建（含重试）→ 轮询 → 返回成片 URL。"""
        frame_rate = int(kwargs.get("frame_rate", self._settings.agnes_video_frame_rate))
        max_frames = int(kwargs.get("max_frames", self._settings.agnes_video_max_frames))
        num_frames = int(
            kwargs.get(
                "num_frames",
                duration_to_num_frames(duration, frame_rate, max_frames),
            )
        )
        width_kw = kwargs.get("width")
        height_kw = kwargs.get("height")
        if width_kw is not None and height_kw is not None:
            width, height = int(width_kw), int(height_kw)
        else:
            aspect_ratio = str(kwargs.get("aspect_ratio", "9:16"))
            width, height = aspect_to_video_size(aspect_ratio)

        video_id = await self._create_video_with_retry(
            image_url, prompt, num_frames, frame_rate, width, height
        )
        url = await self._poll_video(video_id)
        return VideoResult(url=url, duration=duration)
