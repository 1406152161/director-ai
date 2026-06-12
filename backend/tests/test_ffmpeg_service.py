# @author zhangzhihao
"""FFmpeg 服务单元测试（mock subprocess，不真正调用 ffmpeg）。"""

from unittest.mock import MagicMock

import pytest
from app.services.ffmpeg_service import FFmpegNotFoundError, FFmpegService


@pytest.fixture
def ffmpeg_svc():
    return FFmpegService()


def test_compose_shot_clip_command(ffmpeg_svc, monkeypatch, tmp_path):
    monkeypatch.setattr("app.services.ffmpeg_service.shutil.which", lambda _: "/usr/bin/ffmpeg")
    mock_run = MagicMock()
    monkeypatch.setattr("app.services.ffmpeg_service.subprocess.run", mock_run)

    video = tmp_path / "video.mp4"
    audio = tmp_path / "audio.mp3"
    output = tmp_path / "clip.mp4"
    video.write_bytes(b"fake")
    audio.write_bytes(b"fake")

    ffmpeg_svc.compose_shot_clip(
        video,
        audio,
        "测试旁白",
        output,
        target_duration=5.0,
        target_width=768,
        target_height=1344,
    )

    mock_run.assert_called_once()
    cmd = mock_run.call_args[0][0]
    assert cmd[0] == "/usr/bin/ffmpeg"
    assert "-filter_complex" in cmd
    fc_idx = cmd.index("-filter_complex") + 1
    filter_complex = cmd[fc_idx]
    assert "scale=768:1344" in filter_complex
    assert "pad=768:1344" in filter_complex
    assert str(video) in cmd
    assert str(audio) in cmd
    assert str(output) in cmd
    assert "5.0" in cmd or "5" in cmd


def test_probe_duration(ffmpeg_svc, monkeypatch, tmp_path):
    audio = tmp_path / "audio.mp3"
    audio.write_bytes(b"fake")

    def fake_which(name):
        return "/usr/bin/ffprobe" if name == "ffprobe" else None

    monkeypatch.setattr("app.services.ffmpeg_service.shutil.which", fake_which)
    mock_run = MagicMock(return_value=MagicMock(stdout="6.5\n"))
    monkeypatch.setattr("app.services.ffmpeg_service.subprocess.run", mock_run)

    duration = ffmpeg_svc.probe_duration(audio, fallback=4.0)
    assert duration == 6.5
    mock_run.assert_called_once()


def test_probe_duration_fallback(ffmpeg_svc, monkeypatch, tmp_path):
    audio = tmp_path / "missing.mp3"
    monkeypatch.setattr("app.services.ffmpeg_service.shutil.which", lambda _: None)
    assert ffmpeg_svc.probe_duration(audio, fallback=4.0) == 4.0


def test_concat_clips_command(ffmpeg_svc, monkeypatch, tmp_path):
    monkeypatch.setattr("app.services.ffmpeg_service.shutil.which", lambda _: "/usr/bin/ffmpeg")
    mock_run = MagicMock()
    monkeypatch.setattr("app.services.ffmpeg_service.subprocess.run", mock_run)

    clip1 = tmp_path / "c1.mp4"
    clip2 = tmp_path / "c2.mp4"
    clip1.write_bytes(b"fake")
    clip2.write_bytes(b"fake")
    output = tmp_path / "final.mp4"

    ffmpeg_svc.concat_clips([clip1, clip2], output)

    mock_run.assert_called_once()
    cmd = mock_run.call_args[0][0]
    assert cmd[0] == "/usr/bin/ffmpeg"
    assert "-f" in cmd
    assert "concat" in cmd
    assert str(output) in cmd


def test_ffmpeg_not_found(ffmpeg_svc, monkeypatch, tmp_path):
    monkeypatch.setattr("app.services.ffmpeg_service.shutil.which", lambda _: None)

    with pytest.raises(FFmpegNotFoundError, match="未找到 ffmpeg"):
        ffmpeg_svc.compose_shot_clip(
            tmp_path / "v.mp4",
            tmp_path / "a.mp3",
            "旁白",
            tmp_path / "out.mp4",
            target_duration=4.0,
            target_width=768,
            target_height=1344,
        )
