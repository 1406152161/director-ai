# @author zhangzhihao
"""TTS 服务单元测试（mock edge-tts）。"""

from pathlib import Path

import pytest
from app.services.tts_service import TTSService


class MockCommunicate:
    def __init__(self, text: str, voice: str) -> None:
        self.text = text
        self.voice = voice
        self.saved_path: str | None = None

    async def save(self, path: str) -> None:
        self.saved_path = path
        Path(path).write_bytes(b"\xff\xfb" + b"\x00" * 100)


@pytest.mark.asyncio
async def test_tts_synthesize_calls_edge_tts(monkeypatch, tmp_path):
    captured: dict = {}

    def mock_communicate(text, voice):
        captured["text"] = text
        captured["voice"] = voice
        return MockCommunicate(text, voice)

    monkeypatch.setattr("edge_tts.Communicate", mock_communicate)

    svc = TTSService()
    output = tmp_path / "out.mp3"
    result = await svc.synthesize("你好，世界", output, voice="zh-CN-XiaoxiaoNeural")

    assert captured["text"] == "你好，世界"
    assert captured["voice"] == "zh-CN-XiaoxiaoNeural"
    assert result.audio_path == output
    assert result.duration >= 1.0
    assert output.exists()
