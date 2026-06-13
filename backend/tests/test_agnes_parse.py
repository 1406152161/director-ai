# @author zhangzhihao
"""agnes_parse 单元测试。"""

import pytest

from app.providers.video.agnes_parse import extract_completed_video_url


def test_extract_remixed_url():
    url = extract_completed_video_url(
        {"status": "completed", "remixed_from_video_id": "https://cdn.example/a.mp4"},
        "https://apihub.agnes-ai.com",
    )
    assert url == "https://cdn.example/a.mp4"


def test_extract_fallback_video_url():
    url = extract_completed_video_url(
        {"status": "completed", "video_url": "https://cdn.example/b.mp4"},
        "https://apihub.agnes-ai.com",
    )
    assert url == "https://cdn.example/b.mp4"


def test_extract_relative_path():
    url = extract_completed_video_url(
        {"status": "completed", "url": "/files/video.mp4"},
        "https://apihub.agnes-ai.com",
    )
    assert url == "https://apihub.agnes-ai.com/files/video.mp4"


def test_extract_missing_raises():
    with pytest.raises(ValueError, match="缺少可下载"):
        extract_completed_video_url({"status": "completed"}, "https://apihub.agnes-ai.com")
