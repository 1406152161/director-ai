# @author zhangzhihao
"""FFmpeg 视频合成服务：单镜合成 + 多镜拼接。"""

import logging
import shutil
import subprocess
from pathlib import Path

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)


class FFmpegNotFoundError(Exception):
    """本地未安装 ffmpeg。"""


class FFmpegService:
    """通过 subprocess 调用 ffmpeg 完成视频合成。"""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    def _ensure_ffmpeg(self) -> str:
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            raise FFmpegNotFoundError(
                "未找到 ffmpeg，请先安装并加入 PATH。"
                "Windows: winget install ffmpeg；macOS: brew install ffmpeg"
            )
        return ffmpeg

    def probe_duration(self, media_path: Path, fallback: float = 0.0) -> float:
        """用 ffprobe 探测媒体时长（秒），失败时回退 fallback。"""
        ffprobe = shutil.which("ffprobe")
        if not ffprobe or not media_path.exists():
            return fallback
        try:
            result = subprocess.run(
                [
                    ffprobe,
                    "-v", "error",
                    "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1",
                    str(media_path),
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            return max(0.0, float(result.stdout.strip()))
        except (subprocess.CalledProcessError, ValueError):
            return fallback

    def _font_path(self) -> str | None:
        if self._settings.ffmpeg_font_path:
            return self._settings.ffmpeg_font_path
        bundled = (
            Path(__file__).resolve().parents[2]
            / "assets"
            / "fonts"
            / "NotoSansSC-Regular.otf"
        )
        if bundled.exists():
            return str(bundled)
        return None

    @staticmethod
    def _write_srt(narration: str, duration: float, srt_path: Path) -> None:
        """生成单条字幕 SRT 文件。"""
        end = _format_srt_time(duration)
        content = (
            "1\n"
            f"00:00:00,000 --> {end}\n"
            f"{narration.strip()}\n"
        )
        srt_path.write_text(content, encoding="utf-8")

    def compose_shot_clip(
        self,
        video_path: Path,
        audio_path: Path,
        narration_cn: str,
        output_path: Path,
        target_duration: float,
        target_width: int,
        target_height: int,
    ) -> Path:
        """单镜合成：统一分辨率 + 视频 + 配音 + 硬字幕，时长对齐。"""
        ffmpeg = self._ensure_ffmpeg()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        srt_path = output_path.with_suffix(".srt")
        self._write_srt(narration_cn, target_duration, srt_path)

        # 统一分辨率后时长对齐：视频不足定格末帧，音频不足静音补足
        filter_parts = [
            (
                f"[0:v]scale={target_width}:{target_height}:"
                f"force_original_aspect_ratio=decrease,"
                f"pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2,"
                f"tpad=stop_mode=clone:stop_duration={target_duration}[vpad]"
            ),
            f"[1:a]apad=whole_dur={target_duration}[apad]",
        ]

        font = self._font_path()
        srt_escaped = _escape_subtitles_path(srt_path)
        if font:
            font_escaped = _escape_subtitles_path(Path(font))
            subtitle_filter = (
                f"[vpad]subtitles='{srt_escaped}':"
                f"force_style='FontName=Noto Sans SC,FontSize=24',"
                f"fontsdir='{font_escaped.parent}'[vout]"
            )
        else:
            subtitle_filter = f"[vpad]subtitles='{srt_escaped}'[vout]"

        filter_parts.append(subtitle_filter)
        filter_complex = ";".join(filter_parts)

        cmd = [
            ffmpeg,
            "-y",
            "-i", str(video_path),
            "-i", str(audio_path),
            "-filter_complex", filter_complex,
            "-map", "[vout]",
            "-map", "[apad]",
            "-t", str(target_duration),
            "-c:v", "libx264",
            "-c:a", "aac",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            str(output_path),
        ]

        logger.info("FFmpeg 单镜合成: %s", " ".join(cmd))
        subprocess.run(cmd, check=True, capture_output=True)
        return output_path

    def concat_clips(self, clip_paths: list[Path], output_path: Path) -> Path:
        """拼接多镜片段为竖屏 9:16 成片。"""
        ffmpeg = self._ensure_ffmpeg()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        list_file = output_path.with_suffix(".txt")
        lines = [f"file '{p.resolve().as_posix()}'" for p in clip_paths]
        list_file.write_text("\n".join(lines), encoding="utf-8")

        cmd = [
            ffmpeg,
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(list_file),
            "-c", "copy",
            "-movflags", "+faststart",
            str(output_path),
        ]

        logger.info("FFmpeg 拼接成片: %s", " ".join(cmd))
        subprocess.run(cmd, check=True, capture_output=True)
        return output_path


def _format_srt_time(seconds: float) -> str:
    total_ms = int(seconds * 1000)
    hours, rem = divmod(total_ms, 3600_000)
    minutes, rem = divmod(rem, 60_000)
    secs, ms = divmod(rem, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"


def _escape_subtitles_path(path: Path) -> str:
    """转义 subtitles 滤镜路径中的特殊字符（Windows 兼容）。"""
    return str(path.resolve()).replace("\\", "/").replace(":", "\\:")
