# @author zhangzhihao
"""远程媒资下载：重试、Agnes 鉴权、本地 outputs 复制。"""

import asyncio
import logging
from pathlib import Path
from urllib.parse import urlparse

import httpx

from app.providers.exceptions import ProviderError

logger = logging.getLogger(__name__)

_DEFAULT_TIMEOUT = 180.0
_DEFAULT_RETRIES = 3
_BACKOFF_BASE = 2.0


def _build_download_headers(url: str, auth_token: str | None) -> dict[str, str]:
    """Agnes 域名的下载链接可能需要 Bearer 鉴权。"""
    if not auth_token:
        return {}
    host = urlparse(url).netloc.lower()
    if host and ("agnes-ai.com" in host or "apihub" in host):
        return {"Authorization": f"Bearer {auth_token}"}
    return {}


def _copy_local_outputs(url: str, dest: Path, outputs_dir: str) -> bool:
    """复制 /outputs/ 本地静态文件，成功返回 True。"""
    if not url.startswith("/outputs/"):
        return False
    rel = url.removeprefix("/outputs/").lstrip("/")
    src = Path(outputs_dir) / rel
    if not src.is_file():
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(src.read_bytes())
    return True


def _is_retryable(exc: Exception) -> bool:
    return isinstance(
        exc,
        (
            httpx.ConnectError,
            httpx.ReadTimeout,
            httpx.WriteTimeout,
            httpx.ConnectTimeout,
            httpx.RemoteProtocolError,
            httpx.PoolTimeout,
        ),
    )


async def download_media_file(
    url: str,
    dest: Path,
    *,
    outputs_dir: str = "outputs",
    timeout: float = _DEFAULT_TIMEOUT,
    max_retries: int = _DEFAULT_RETRIES,
    auth_token: str | None = None,
) -> Path:
    """
    下载远程媒资到 dest；本地 /outputs/ 路径则直接复制。
    网络类错误指数退避重试。
    """
    dest.parent.mkdir(parents=True, exist_ok=True)

    if url.startswith("file://"):
        src = Path(url.removeprefix("file://"))
        if src.is_file():
            dest.write_bytes(src.read_bytes())
            return dest
        raise ProviderError(f"本地文件不存在: {url}")

    if _copy_local_outputs(url, dest, outputs_dir):
        return dest

    if "example.com" in url or url.startswith("mock://"):
        dest.write_bytes(b"fake-video-content")
        return dest

    if not url.startswith(("http://", "https://")):
        raise ProviderError(f"无法下载媒资，URL 无效: {url[:120]}")

    headers = _build_download_headers(url, auth_token)
    last_exc: Exception | None = None

    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(
                timeout=timeout,
                follow_redirects=True,
            ) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                dest.write_bytes(response.content)
                return dest
        except httpx.HTTPStatusError as exc:
            raise ProviderError(
                f"下载媒资 HTTP 错误 ({exc.response.status_code}): {url[:120]}"
            ) from exc
        except Exception as exc:
            if not _is_retryable(exc):
                raise ProviderError(f"下载媒资失败: {url[:120]} — {exc}") from exc
            last_exc = exc
            if attempt == max_retries - 1:
                break
            delay = _BACKOFF_BASE ** (attempt + 1)
            logger.warning(
                "媒资下载第 %d 次失败，%ss 后重试 url=%s err=%s",
                attempt + 1,
                delay,
                url[:120],
                exc,
            )
            await asyncio.sleep(delay)

    assert last_exc is not None
    raise ProviderError(
        f"下载媒资网络失败（已重试 {max_retries} 次）: {url[:120]} — {last_exc}"
    ) from last_exc
