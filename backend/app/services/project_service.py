# @author zhangzhihao
"""业务服务层占位。"""

from app.schemas.project import ProjectCreate, ProjectResponse


class ProjectService:
    """项目业务逻辑，M1 接入 Pipeline 与持久化。"""

    async def create_project(self, body: ProjectCreate) -> ProjectResponse:
        raise NotImplementedError("M1 实现")
