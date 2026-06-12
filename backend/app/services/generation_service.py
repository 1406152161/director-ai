# @author zhangzhihao
"""M2/M3 生成编排：脚本 → 资产 → 配图 → 视频+配音 → FFmpeg 合成成片。"""

import asyncio
import logging
from pathlib import Path

import httpx

from app.core.config import get_settings
from app.core.constants import aspect_to_video_size
from app.core.database import SessionLocal
from app.models.project import Shot
from app.providers.registry import get_video_provider
from app.services.asset_service import AssetService
from app.services.ffmpeg_service import FFmpegService
from app.services.image_service import ImageService
from app.services.project_service import ProjectService
from app.services.script_service import ScriptService, ShotData
from app.services.tts_service import TTSService

logger = logging.getLogger(__name__)


async def _download_file(url: str, dest: Path) -> Path:
    """下载远程媒资到本地。mock/example URL 写入占位内容供测试。"""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if url.startswith("/outputs/") or url.startswith("file://"):
        # 本地静态资源路径，复制或写入占位
        local = url.removeprefix("file://")
        src = Path(get_settings().outputs_dir).parent / local.lstrip("/")
        if src.exists():
            dest.write_bytes(src.read_bytes())
            return dest
        dest.write_bytes(b"fake-video-content")
        return dest
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


def _local_output_url(project_id: str, *parts: str) -> str:
    return "/outputs/" + "/".join([project_id, *parts])


async def run_generation(project_id: str) -> None:
    """后台任务入口：按 coherent_mode 选择 M2 或 M3 编排。"""
    settings = get_settings()
    if settings.coherent_mode:
        await _run_m3_pipeline(project_id)
    else:
        await _run_m2_pipeline(project_id)


async def _run_m2_pipeline(project_id: str) -> None:
    """M2：无资产、并行视频、硬拼接。"""
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
            project_svc.update_status(project_id, "scripting", 10)
            script = await script_svc.generate_script(
                project.story, project.style, project.duration
            )
            project_svc.save_script(project_id, script.title, script.shots)
            project_svc.update_status(project_id, "scripting", 20)

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
                            audio_url=_local_output_url(
                                project_id, f"shot_{shot.index}", "narration.mp3"
                            ),
                        )

                async with video_lock:
                    completed_video += 1
                    current = completed_video
                async with db_lock:
                    await project_svc.update_videoing_progress(
                        project_id, current, total_shots
                    )

            await asyncio.gather(*[_process_shot(s) for s in shots])

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
                    _local_output_url(project_id, f"shot_{shot.index}", "clip.mp4"),
                )

            final_path = out_dir / "final.mp4"
            ffmpeg_svc.concat_clips(clip_paths, final_path)
            output_url = _local_output_url(project_id, "final.mp4")
            project_svc.mark_completed(project_id, output_url)
            logger.info("项目生成完成(M2): %s → %s", project_id, output_url)

        except Exception as exc:
            logger.exception("项目生成失败: %s", project_id)
            project_svc.set_failed(project_id, str(exc))

    finally:
        db.close()


async def _run_m3_pipeline(project_id: str) -> None:
    """M3：资产一致性 + 链式尾帧 + xfade + 连续旁白。"""
    db = SessionLocal()
    try:
        project_svc = ProjectService(db)
        script_svc = ScriptService()
        asset_svc = AssetService()
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
        xfade = settings.xfade_duration

        try:
            # ① 脚本
            project_svc.update_status(project_id, "scripting", 10)
            script = await script_svc.generate_script(
                project.story, project.style, project.duration
            )
            project_svc.save_script(
                project_id, script.title, script.shots, script.assets
            )
            project_svc.update_status(project_id, "scripting", 20)

            # ② 资产生成
            project_svc.update_status(project_id, "asseting", 20)
            db_assets = project_svc.get_assets_for_project(project_id)
            asset_items = [
                {
                    "asset_key": a.asset_key,
                    "description_en": a.description_en,
                    "name_cn": a.name_cn,
                }
                for a in db_assets
            ]

            async def on_asset_done(
                asset_key: str, url: str, completed: int, total: int
            ) -> None:
                project_svc.save_asset_image(project_id, asset_key, url)
                await project_svc.update_asseting_progress(project_id, completed, total)

            if asset_items:
                await asset_svc.generate_assets(
                    asset_items,
                    project.aspect_ratio,
                    on_done=on_asset_done,
                )

            url_map = project_svc.build_asset_url_map(project_id)

            # ③ 关键帧图生图
            project_svc.update_status(project_id, "imaging", 30)

            async def on_keyframe_done(
                shot: ShotData, url: str, completed: int, total: int
            ) -> None:
                project_svc.save_shot_image(project_id, shot.index, url)
                await project_svc.update_imaging_progress(project_id, completed, total)

            await image_svc.generate_keyframes(
                script.shots,
                script.assets,
                url_map,
                project.style,
                project.aspect_ratio,
                on_shot_done=on_keyframe_done,
            )

            # ④ 串行链式视频 + 并行 TTS
            project_svc.update_status(project_id, "videoing", 50)
            shots = (
                db.query(Shot)
                .filter(Shot.project_id == project_id)
                .order_by(Shot.index)
                .all()
            )
            total_shots = len(shots)
            prev_local_video: Path | None = None

            for idx, shot in enumerate(shots):
                shot_dir = out_dir / f"shot_{shot.index}"
                shot_dir.mkdir(parents=True, exist_ok=True)
                motion = shot.motion_prompt_en or shot.image_prompt_en or "gentle camera movement"

                # 确定图生视频输入图
                if idx == 0:
                    video_input_url = shot.image_url or ""
                else:
                    assert prev_local_video is not None
                    tail_frame = shot_dir / "chain_input.jpg"
                    ffmpeg_svc.extract_last_frame(prev_local_video, tail_frame)
                    video_input_url = _local_output_url(
                        project_id, f"shot_{shot.index}", "chain_input.jpg"
                    )

                audio_path = shot_dir / "narration.mp3"
                video_task = video_provider.image_to_video(
                    video_input_url,
                    motion,
                    shot.duration,
                    aspect_ratio=project.aspect_ratio,
                )
                tts_task = tts_svc.synthesize(shot.narration_cn, audio_path)
                video_result, _tts_result = await asyncio.gather(video_task, tts_task)

                local_video = shot_dir / "raw_video.mp4"
                await _download_file(video_result.url, local_video)
                prev_local_video = local_video

                project_svc.save_shot_media(
                    project_id,
                    shot.index,
                    video_url=video_result.url,
                    audio_url=_local_output_url(
                        project_id, f"shot_{shot.index}", "narration.mp3"
                    ),
                )
                await project_svc.update_videoing_progress(
                    project_id, idx + 1, total_shots
                )

            # ⑤ 合成：单镜预览 + xfade 成片 + 连续旁白
            project_svc.update_status(project_id, "synthesizing", 75)
            target_width, target_height = aspect_to_video_size(project.aspect_ratio)
            video_only_paths: list[Path] = []
            audio_paths: list[Path] = []

            for shot in shots:
                shot_dir = out_dir / f"shot_{shot.index}"
                local_video = shot_dir / "raw_video.mp4"
                audio_path = shot_dir / "narration.mp3"
                clip_path = shot_dir / "clip.mp4"
                video_only_path = shot_dir / "clip_video.mp4"
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
                ffmpeg_svc.compose_shot_video_only(
                    local_video,
                    shot.narration_cn,
                    video_only_path,
                    target_duration,
                    target_width,
                    target_height,
                )
                video_only_paths.append(video_only_path)
                audio_paths.append(audio_path)
                project_svc.save_shot_clip(
                    project_id,
                    shot.index,
                    _local_output_url(project_id, f"shot_{shot.index}", "clip.mp4"),
                )

            xfade_path = out_dir / "xfade_video.mp4"
            ffmpeg_svc.concat_clips_xfade(video_only_paths, xfade_path, xfade)

            continuous_audio = out_dir / "continuous_narration.m4a"
            ffmpeg_svc.build_continuous_audio(audio_paths, continuous_audio)

            final_path = out_dir / "final.mp4"
            ffmpeg_svc.compose_final_with_continuous_audio(
                xfade_path, continuous_audio, final_path
            )
            output_url = _local_output_url(project_id, "final.mp4")
            project_svc.mark_completed(project_id, output_url)
            logger.info("项目生成完成(M3): %s → %s", project_id, output_url)

        except Exception as exc:
            logger.exception("项目生成失败: %s", project_id)
            project_svc.set_failed(project_id, str(exc))

    finally:
        db.close()
