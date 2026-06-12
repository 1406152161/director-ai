# @author zhangzhihao
"""M2 生成编排：脚本 → 配图 → 视频+配音 → FFmpeg 合成成片。"""

import asyncio
import logging
from pathlib import Path

import httpx

from app.core.config import get_settings
from app.core.constants import aspect_to_video_size
from app.core.database import SessionLocal
from app.models.project import Shot
from app.providers.registry import get_video_provider
from app.services.ffmpeg_service import FFmpegService
from app.services.image_service import ImageService
from app.services.project_service import ProjectService
from app.services.script_service import ScriptService, ShotData
from app.services.tts_service import TTSService

logger = logging.getLogger(__name__)


async def _download_file(url: str, dest: Path) -> Path:
    """下载远程媒资到本地。mock/example URL 写入占位内容供测试。"""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if "example.com" in url or url.startswith("mock://"):
        dest.write_bytes(b"fake-video-content")
        return dest
    async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
        response = await client.get(url)
        response.raise_for_status()
        dest.write_bytes(response.content)
    return dest


def _outputs_root() -> Path:
    return Path(get_settings().outputs_dir)


async def run_generation(project_id: str) -> None:
    """后台任务：pending → scripting → imaging → videoing → synthesizing → completed。"""
    db = SessionLocal()
    try:
        project_svc = ProjectService(db)
        script_svc = ScriptService()
        image_svc = ImageService()
        tts_svc = TTSService()
        ffmpeg_svc = FFmpegService()
        video_provider = get_video_provider()
        settings = get_settings()

        project = project_svc.get_project(project_id)
        if not project:
            logger.error("项目不存在: %s", project_id)
            return

        out_dir = _outputs_root() / project_id

        try:
            # ① 脚本生成
            project_svc.update_status(project_id, "scripting", 10)
            script = await script_svc.generate_script(
                project.story, project.style, project.duration
            )
            project_svc.save_script(project_id, script.title, script.shots)
            project_svc.update_status(project_id, "scripting", 20)

            # ② 逐镜头配图
            project_svc.update_status(project_id, "imaging", 20)

            async def on_image_done(
                shot: ShotData, url: str, completed: int, total: int
            ) -> None:
                project_svc.save_shot_image(project_id, shot.index, url)
                await project_svc.update_imaging_progress(project_id, completed, total)

            await image_svc.generate_images(
                script.shots,
                project.style,
                project.aspect_ratio,
                on_shot_done=on_image_done,
            )

            # ③ 每镜头并发：图生视频 ‖ TTS 配音
            project_svc.update_status(project_id, "videoing", 40)
            shots = (
                db.query(Shot)
                .filter(Shot.project_id == project_id)
                .order_by(Shot.index)
                .all()
            )
            total_shots = len(shots)
            sem = asyncio.Semaphore(settings.video_max_concurrency)
            completed_video = 0
            video_lock = asyncio.Lock()
            db_lock = asyncio.Lock()

            async def _process_shot(shot: Shot) -> None:
                nonlocal completed_video
                shot_dir = out_dir / f"shot_{shot.index}"
                motion = shot.motion_prompt_en or shot.image_prompt_en or "gentle camera movement"

                async with sem:
                    video_task = video_provider.image_to_video(
                        shot.image_url or "",
                        motion,
                        shot.duration,
                        aspect_ratio=project.aspect_ratio,
                    )
                    audio_path = shot_dir / "narration.mp3"
                    tts_task = tts_svc.synthesize(shot.narration_cn, audio_path)

                    video_result, tts_result = await asyncio.gather(video_task, tts_task)

                    local_video = shot_dir / "raw_video.mp4"
                    await _download_file(video_result.url, local_video)

                    async with db_lock:
                        project_svc.save_shot_media(
                            project_id,
                            shot.index,
                            video_url=video_result.url,
                            audio_url=f"/outputs/{project_id}/shot_{shot.index}/narration.mp3",
                        )

                async with video_lock:
                    completed_video += 1
                    current = completed_video
                async with db_lock:
                    await project_svc.update_videoing_progress(
                        project_id, current, total_shots
                    )

            await asyncio.gather(*[_process_shot(s) for s in shots])

            # ④ FFmpeg 单镜合成 + 拼接
            project_svc.update_status(project_id, "synthesizing", 75)
            clip_paths: list[Path] = []
            target_width, target_height = aspect_to_video_size(project.aspect_ratio)

            for shot in shots:
                shot_dir = out_dir / f"shot_{shot.index}"
                local_video = shot_dir / "raw_video.mp4"
                audio_path = shot_dir / "narration.mp3"
                clip_path = shot_dir / "clip.mp4"
                audio_duration = ffmpeg_svc.probe_duration(
                    audio_path, fallback=float(shot.duration)
                )
                target_duration = max(float(shot.duration), audio_duration, 1.0)

                ffmpeg_svc.compose_shot_clip(
                    local_video,
                    audio_path,
                    shot.narration_cn,
                    clip_path,
                    target_duration,
                    target_width,
                    target_height,
                )
                clip_paths.append(clip_path)
                project_svc.save_shot_clip(
                    project_id,
                    shot.index,
                    f"/outputs/{project_id}/shot_{shot.index}/clip.mp4",
                )

            final_path = out_dir / "final.mp4"
            ffmpeg_svc.concat_clips(clip_paths, final_path)
            output_url = f"/outputs/{project_id}/final.mp4"
            project_svc.mark_completed(project_id, output_url)
            logger.info("项目生成完成: %s → %s", project_id, output_url)

        except Exception as exc:
            logger.exception("项目生成失败: %s", project_id)
            project_svc.set_failed(project_id, str(exc))

    finally:
        db.close()
