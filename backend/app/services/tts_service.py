# @author zhangzhihao
"""Edge-TTS 旁白合成服务。"""

import logging
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)


@dataclass
class TTSSynthesisResult:
    """TTS 合成结果。"""

    audio_path: Path
    duration: float


class TTSService:
    """使用 edge-tts 将中文旁白合成为 mp3。"""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    async def synthesize(
        self,
        text: str,
        output_path: Path,
        voice: str | None = None,
    ) -> TTSSynthesisResult:
        """合成旁白 mp3，返回本地路径与时长（秒）。"""
        import edge_tts

        voice = voice or self._settings.tts_voice
        output_path.parent.mkdir(parents=True, exist_ok=True)

        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(str(output_path))

        duration = self._probe_audio_duration(output_path)
        if duration <= 0:
            duration = max(1.0, len(text.strip()) * 0.25)
        logger.info("TTS 合成完成 voice=%s duration=%.2fs path=%s", voice, duration, output_path)
        return TTSSynthesisResult(audio_path=output_path, duration=duration)

    def _probe_audio_duration(self, audio_path: Path) -> float:
        """用 ffprobe 读取实际音频时长（秒）。"""
        ffprobe = shutil.which("ffprobe")
        if not ffprobe or not audio_path.exists():
            return 0.0
        try:
            result = subprocess.run(
                [
                    ffprobe,
                    "-v", "error",
                    "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1",
                    str(audio_path),
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            return max(0.1, float(result.stdout.strip()))
        except (subprocess.CalledProcessError, ValueError):
            return 0.0

    def _estimate_duration(self, text: str, audio_path: Path) -> float:
        """兼容旧调用：优先 ffprobe 实际时长。"""
        probed = self._probe_audio_duration(audio_path)
        if probed > 0:
            return probed
        return max(1.0, len(text.strip()) * 0.25)
