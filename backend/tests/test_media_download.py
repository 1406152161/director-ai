# @author zhangzhihao
"""media_download 单元测试。"""

import pytest
import httpx

from app.providers.exceptions import ProviderError
from app.utils.media_download import download_media_file


@pytest.mark.asyncio
async def test_copy_local_outputs(tmp_path):
    src = tmp_path / "outputs" / "p1" / "raw.mp4"
    src.parent.mkdir(parents=True)
    src.write_bytes(b"local-video")
    dest = tmp_path / "dest.mp4"

    await download_media_file(
        "/outputs/p1/raw.mp4",
        dest,
        outputs_dir=str(tmp_path / "outputs"),
    )
    assert dest.read_bytes() == b"local-video"


@pytest.mark.asyncio
async def test_download_retries_on_connect_error(monkeypatch, tmp_path):
    dest = tmp_path / "out.mp4"
    attempts = 0

    class MockClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def get(self, url, headers=None):
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                raise httpx.ConnectError("tls failed")
            request = httpx.Request("GET", url)
            return httpx.Response(200, request=request, content=b"ok")

    async def noop_sleep(_):
        return None

    monkeypatch.setattr(httpx, "AsyncClient", lambda **kw: MockClient())
    monkeypatch.setattr("app.utils.media_download.asyncio.sleep", noop_sleep)

    await download_media_file(
        "https://cdn.test.invalid/v.mp4",
        dest,
        max_retries=3,
    )
    assert dest.read_bytes() == b"ok"
    assert attempts == 3


@pytest.mark.asyncio
async def test_download_exhausted_retries(monkeypatch, tmp_path):
    dest = tmp_path / "out.mp4"

    class MockClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def get(self, url, headers=None):
            raise httpx.ConnectError("always fail")

    async def noop_sleep(_):
        return None

    monkeypatch.setattr(httpx, "AsyncClient", lambda **kw: MockClient())
    monkeypatch.setattr("app.utils.media_download.asyncio.sleep", noop_sleep)

    with pytest.raises(ProviderError, match="网络失败"):
        await download_media_file(
            "https://cdn.test.invalid/v.mp4",
            dest,
            max_retries=2,
        )
