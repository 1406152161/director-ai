# @author zhangzhihao
"""media_input 工具单元测试。"""

import base64

import pytest

from app.utils.media_input import (
    normalize_video_image_input,
    path_to_base64,
    path_to_data_uri,
    resolve_local_image_path,
)


def test_resolve_outputs_path(tmp_path):
    img = tmp_path / "proj" / "shot_2" / "chain_input.jpg"
    img.parent.mkdir(parents=True)
    img.write_bytes(b"\xff\xd8\xff fake jpeg")

    resolved = resolve_local_image_path(
        "/outputs/proj/shot_2/chain_input.jpg",
        str(tmp_path),
    )
    assert resolved == img


def test_path_to_base64_padding(tmp_path):
    # 任意长度字节编码后 base64 长度必须是 4 的倍数
    for size in (1, 2, 3, 10, 61, 100):
        p = tmp_path / f"img_{size}.jpg"
        p.write_bytes(b"x" * size)
        encoded = path_to_base64(p)
        assert len(encoded) % 4 == 0
        assert base64.b64decode(encoded) == p.read_bytes()


def test_normalize_keeps_http_url():
    url = "https://cdn.example.com/a.png"
    assert normalize_video_image_input(url, "outputs") == url


def test_normalize_local_outputs_to_base64(tmp_path):
    img = tmp_path / "p1" / "shot_2" / "chain_input.jpg"
    img.parent.mkdir(parents=True)
    img.write_bytes(b"\xff\xd8\xff tail frame")

    result = normalize_video_image_input(
        "/outputs/p1/shot_2/chain_input.jpg",
        str(tmp_path),
    )
    assert not result.startswith("/outputs/")
    assert len(result) % 4 == 0
    assert base64.b64decode(result) == img.read_bytes()


def test_normalize_missing_local_raises(tmp_path):
    with pytest.raises(ValueError, match="无法解析"):
        normalize_video_image_input(
            "/outputs/p1/shot_9/missing.jpg",
            str(tmp_path),
        )


def test_path_to_data_uri_format(tmp_path):
    p = tmp_path / "a.png"
    p.write_bytes(b"\x89PNG")
    uri = path_to_data_uri(p)
    assert uri.startswith("data:image/png;base64,")
