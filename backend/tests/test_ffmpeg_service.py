# @author zhangzhihao
"""FFmpeg 服务单元测试（mock subprocess，不真正调用 ffmpeg）。"""

import subprocess

import pytest
from app.services.ffmpeg_service import FFmpegNotFoundError, FFmpegService, _escape_ffmpeg_path


def _patch_ffmpeg_run(monkeypatch):
    calls: list[list[str]] = []

    def run(cmd, **kwargs):
        calls.append(cmd)
        stdout = "6.5\n" if cmd and "ffprobe" in str(cmd[0]) else ""
        return subprocess.CompletedProcess(cmd, 0, stdout=stdout, stderr="")

    monkeypatch.setattr("app.services.ffmpeg_service.subprocess.run", run)
    return calls


@pytest.fixture
def ffmpeg_svc():
    return FFmpegService()


def test_compose_shot_clip_command(ffmpeg_svc, monkeypatch, tmp_path):
    monkeypatch.setattr("app.services.ffmpeg_service.shutil.which", lambda _: "/usr/bin/ffmpeg")
    calls = _patch_ffmpeg_run(monkeypatch)

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

    assert len(calls) == 1
    cmd = calls[0]
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
    calls = _patch_ffmpeg_run(monkeypatch)

    duration = ffmpeg_svc.probe_duration(audio, fallback=4.0)
    assert duration == 6.5
    assert len(calls) == 1


def test_probe_duration_fallback(ffmpeg_svc, monkeypatch, tmp_path):
    audio = tmp_path / "missing.mp3"
    monkeypatch.setattr("app.services.ffmpeg_service.shutil.which", lambda _: None)
    assert ffmpeg_svc.probe_duration(audio, fallback=4.0) == 4.0


def test_concat_clips_command(ffmpeg_svc, monkeypatch, tmp_path):
    monkeypatch.setattr("app.services.ffmpeg_service.shutil.which", lambda _: "/usr/bin/ffmpeg")
    calls = _patch_ffmpeg_run(monkeypatch)

    clip1 = tmp_path / "c1.mp4"
    clip2 = tmp_path / "c2.mp4"
    clip1.write_bytes(b"fake")
    clip2.write_bytes(b"fake")
    output = tmp_path / "final.mp4"

    ffmpeg_svc.concat_clips([clip1, clip2], output)

    assert len(calls) == 1
    cmd = calls[0]
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


def test_extract_last_frame_command(ffmpeg_svc, monkeypatch, tmp_path):
    monkeypatch.setattr("app.services.ffmpeg_service.shutil.which", lambda _: "/usr/bin/ffmpeg")
    calls = _patch_ffmpeg_run(monkeypatch)

    video = tmp_path / "video.mp4"
    output = tmp_path / "last.jpg"
    video.write_bytes(b"fake")

    ffmpeg_svc.extract_last_frame(video, output)

    assert len(calls) == 1
    cmd = calls[0]
    assert "-sseof" in cmd
    assert "-0.1" in cmd
    assert "-frames:v" in cmd
    assert "1" in cmd
    assert str(output) in cmd


def test_compute_xfade_offsets():
    offsets = FFmpegService.compute_xfade_offsets([5.0, 5.0, 5.0], 0.4)
    assert offsets == [4.6, 9.2]


def test_concat_clips_xfade_command(ffmpeg_svc, monkeypatch, tmp_path):
    monkeypatch.setattr("app.services.ffmpeg_service.shutil.which", lambda _: "/usr/bin/ffmpeg")
    calls = _patch_ffmpeg_run(monkeypatch)
    monkeypatch.setattr(
        "app.services.ffmpeg_service.FFmpegService.probe_duration",
        lambda self, p, fallback=0.0: 5.0,
    )

    clip1 = tmp_path / "c1.mp4"
    clip2 = tmp_path / "c2.mp4"
    clip1.write_bytes(b"fake")
    clip2.write_bytes(b"fake")
    output = tmp_path / "final.mp4"

    ffmpeg_svc.concat_clips_xfade([clip1, clip2], output, xfade_duration=0.4)

    assert len(calls) == 1
    cmd = calls[0]
    fc_idx = cmd.index("-filter_complex") + 1
    filter_complex = cmd[fc_idx]
    assert "xfade" in filter_complex
    assert "offset=4.6" in filter_complex


def test_build_continuous_audio_command(ffmpeg_svc, monkeypatch, tmp_path):
    monkeypatch.setattr("app.services.ffmpeg_service.shutil.which", lambda _: "/usr/bin/ffmpeg")
    calls = _patch_ffmpeg_run(monkeypatch)

    a1 = tmp_path / "1.mp3"
    a2 = tmp_path / "2.mp3"
    a1.write_bytes(b"fake")
    a2.write_bytes(b"fake")
    output = tmp_path / "continuous.m4a"

    ffmpeg_svc.build_continuous_audio([a1, a2], output)

    assert len(calls) == 1
    cmd = calls[0]
    fc_idx = cmd.index("-filter_complex") + 1
    filter_complex = cmd[fc_idx]
    assert "concat=n=2:v=0:a=1" in filter_complex


def test_escape_ffmpeg_path_with_spaces():
    escaped = _escape_ffmpeg_path("C:/Program Files/fonts/Noto.ttf")
    assert "Program Files" in escaped
    assert escaped.endswith("Noto.ttf")


def test_run_subprocess_logs_stderr(ffmpeg_svc, monkeypatch, tmp_path):
    monkeypatch.setattr("app.services.ffmpeg_service.shutil.which", lambda _: "/usr/bin/ffmpeg")

    def fail_run(cmd, **kwargs):
        return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="mock ffmpeg error")

    monkeypatch.setattr("app.services.ffmpeg_service.subprocess.run", fail_run)
    video = tmp_path / "video.mp4"
    audio = tmp_path / "audio.mp3"
    video.write_bytes(b"v")
    audio.write_bytes(b"a")
    output = tmp_path / "clip.mp4"
    with pytest.raises(subprocess.CalledProcessError):
        ffmpeg_svc.compose_shot_clip(
            video, audio, "旁白", output, 5.0, 768, 1344
        )
