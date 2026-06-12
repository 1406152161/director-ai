# @author zhangzhihao
"""项目 API 路由。"""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.project import ProjectCreate, ProjectListItem, ProjectResponse
from app.services.generation_service import run_generation
from app.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectListItem])
async def list_projects(db: Session = Depends(get_db)) -> list[ProjectListItem]:
    svc = ProjectService(db)
    projects = svc.list_projects()
    return [svc.to_list_item(p) for p in projects]


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(
    body: ProjectCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> ProjectResponse:
    svc = ProjectService(db)
    project = svc.create_project(body)
    background_tasks.add_task(run_generation, project.id)
    return svc.to_response(project)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, db: Session = Depends(get_db)) -> ProjectResponse:
    svc = ProjectService(db)
    project = svc.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    return svc.to_response(project)
