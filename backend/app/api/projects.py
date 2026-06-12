# @author zhangzhihao
"""项目 CRUD 占位路由。"""

from uuid import uuid4

from fastapi import APIRouter

from app.schemas.project import ProjectCreate, ProjectResponse

router = APIRouter(prefix="/projects", tags=["projects"])

# M0 内存占位，M1 接入数据库
_projects: dict[str, ProjectResponse] = {}


@router.get("", response_model=list[ProjectResponse])
async def list_projects() -> list[ProjectResponse]:
    return list(_projects.values())


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(body: ProjectCreate) -> ProjectResponse:
    project_id = str(uuid4())
    project = ProjectResponse(
        id=project_id,
        story=body.story,
        style=body.style,
        duration=body.duration,
        aspect_ratio=body.aspect_ratio,
        status="pending",
    )
    _projects[project_id] = project
    return project


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str) -> ProjectResponse:
    if project_id not in _projects:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="项目不存在")
    return _projects[project_id]
