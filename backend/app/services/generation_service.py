# @author zhangzhihao
"""M1 生成编排：脚本 → 配图全链路。"""

import logging

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.services.image_service import ImageService
from app.services.project_service import ProjectService
from app.services.script_service import ScriptService

logger = logging.getLogger(__name__)


async def run_generation(project_id: str) -> None:
    """后台任务：执行 pending → scripting → imaging → completed 全流程。"""
    db: Session = SessionLocal()
    try:
        project_svc = ProjectService(db)
        script_svc = ScriptService()
        image_svc = ImageService()

        project = project_svc.get_project(project_id)
        if not project:
            logger.error("项目不存在: %s", project_id)
            return

        try:
            # ① 脚本生成
            project_svc.update_status(project_id, "scripting", 10)
            script = await script_svc.generate_script(
                project.story, project.style, project.duration
            )
            project_svc.save_script(project_id, script.title, script.shots)
            project_svc.update_status(project_id, "scripting", 30)

            # ② 逐镜头配图
            project_svc.update_status(project_id, "imaging", 30)

            async def on_shot_done(
                shot, url: str, completed: int, total: int
            ) -> None:
                project_svc.save_shot_image(project_id, shot.index, url)
                await project_svc.update_imaging_progress(project_id, completed, total)

            await image_svc.generate_images(
                script.shots,
                project.style,
                project.aspect_ratio,
                on_shot_done=on_shot_done,
            )

            project_svc.mark_completed(project_id)
            logger.info("项目生成完成: %s", project_id)

        except Exception as exc:
            logger.exception("项目生成失败: %s", project_id)
            project_svc.set_failed(project_id, str(exc))

    finally:
        db.close()
