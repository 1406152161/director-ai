# @author zhangzhihao
"""项目业务服务：持久化与状态管理。"""

from sqlalchemy.orm import Session, joinedload

from app.models.project import Project, Shot
from app.schemas.project import ProjectCreate, ProjectListItem, ProjectResponse, ShotResponse
from app.services.script_service import ShotData


class ProjectService:
    """项目 CRUD 与分镜落库。"""

    def __init__(self, db: Session) -> None:
        self._db = db

    def create_project(self, body: ProjectCreate) -> Project:
        project = Project(
            story=body.story,
            style=body.style,
            duration=body.duration,
            aspect_ratio=body.aspect_ratio,
            status="pending",
            progress=0,
        )
        self._db.add(project)
        self._db.commit()
        self._db.refresh(project)
        return project

    def get_project(self, project_id: str) -> Project | None:
        return (
            self._db.query(Project)
            .options(joinedload(Project.shots))
            .filter(Project.id == project_id)
            .first()
        )

    def list_projects(self) -> list[Project]:
        return self._db.query(Project).order_by(Project.created_at.desc()).all()

    def update_status(self, project_id: str, status: str, progress: int | None = None) -> None:
        project = self._db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return
        project.status = status
        if progress is not None:
            project.progress = progress
        self._db.commit()

    def set_failed(self, project_id: str, error: str) -> None:
        project = self._db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return
        project.status = "failed"
        project.error = error
        self._db.commit()

    def save_script(self, project_id: str, title: str, shots: list[ShotData]) -> None:
        project = self._db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return

        project.title = title
        # 清除旧镜头（重试场景）
        self._db.query(Shot).filter(Shot.project_id == project_id).delete()

        for shot_data in shots:
            shot = Shot(
                project_id=project_id,
                index=shot_data.index,
                scene_cn=shot_data.scene_cn,
                image_prompt_en=shot_data.image_prompt_en,
                narration_cn=shot_data.narration_cn,
                duration=shot_data.duration,
                status="pending",
            )
            self._db.add(shot)

        self._db.commit()

    async def update_imaging_progress(self, project_id: str, completed: int, total: int) -> None:
        """配图进度：30% 起，占 70% 区间。"""
        progress = 30 + int((completed / total) * 70) if total > 0 else 30
        self.update_status(project_id, "imaging", progress)

    def save_shot_image(self, project_id: str, shot_index: int, image_url: str) -> None:
        shot = (
            self._db.query(Shot)
            .filter(Shot.project_id == project_id, Shot.index == shot_index)
            .first()
        )
        if shot:
            shot.image_url = image_url
            shot.status = "completed"
            self._db.commit()

    def mark_completed(self, project_id: str) -> None:
        self.update_status(project_id, "completed", 100)

    @staticmethod
    def to_response(project: Project) -> ProjectResponse:
        shots = [
            ShotResponse(
                id=s.id,
                index=s.index,
                scene_cn=s.scene_cn,
                image_prompt_en=s.image_prompt_en,
                narration_cn=s.narration_cn,
                duration=s.duration,
                image_url=s.image_url,
                status=s.status,
            )
            for s in sorted(project.shots, key=lambda x: x.index)
        ]
        return ProjectResponse(
            id=project.id,
            story=project.story,
            style=project.style,
            duration=project.duration,
            aspect_ratio=project.aspect_ratio,
            status=project.status,
            progress=project.progress,
            title=project.title,
            error=project.error,
            created_at=project.created_at,
            shots=shots,
        )

    @staticmethod
    def to_list_item(project: Project) -> ProjectListItem:
        return ProjectListItem(
            id=project.id,
            story=project.story,
            style=project.style,
            duration=project.duration,
            aspect_ratio=project.aspect_ratio,
            status=project.status,
            progress=project.progress,
            title=project.title,
            created_at=project.created_at,
        )
