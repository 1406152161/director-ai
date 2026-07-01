# @author zhangzhihao
"""项目 API 路由。"""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_auth_context, optional_owner_id
from app.api.streaming import progress_event_response
from app.core.config import get_settings
from app.core.database import get_db
from app.schemas.project import ProjectCreate, ProjectListItem, ProjectResponse
from app.services.task_dispatch import enqueue_video_generation
from app.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])


def _assert_owner(project, owner_id: str | None) -> None:
    """auth_enabled 时校验资源归属；越权返回 404 避免泄露存在性。"""
    if not get_settings().auth_enabled or owner_id is None:
        return
    if project.owner_id != owner_id:
        raise HTTPException(status_code=404, detail="项目不存在")


@router.get("", response_model=list[ProjectListItem])
async def list_projects(
    db: Session = Depends(get_db),
    owner_id: str | None = Depends(optional_owner_id),
) -> list[ProjectListItem]:
    svc = ProjectService(db)
    projects = svc.list_projects(owner_id)
    return [svc.to_list_item(p) for p in projects]


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(
    body: ProjectCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    ctx=Depends(get_auth_context),
) -> ProjectResponse:
    if get_settings().auth_enabled and ctx is None:
        raise HTTPException(status_code=401, detail="未登录")
    svc = ProjectService(db)
    project = svc.create_project(body, owner_id=ctx.user_id if ctx else None)
    enqueue_video_generation(background_tasks, project.id)
    return svc.to_response(project)


@router.post("/{project_id}/retry", response_model=ProjectResponse)
async def retry_project(
    project_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    owner_id: str | None = Depends(optional_owner_id),
) -> ProjectResponse:
    svc = ProjectService(db)
    project = svc.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    _assert_owner(project, owner_id)
    if project.status != "failed":
        raise HTTPException(status_code=409, detail="仅失败项目可重试")
    svc.reset_for_retry(project_id)
    enqueue_video_generation(background_tasks, project_id)
    project = svc.get_project(project_id)
    return svc.to_response(project)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    db: Session = Depends(get_db),
    owner_id: str | None = Depends(optional_owner_id),
) -> ProjectResponse:
    svc = ProjectService(db)
    project = svc.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    _assert_owner(project, owner_id)
    return svc.to_response(project)


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: str,
    db: Session = Depends(get_db),
    owner_id: str | None = Depends(optional_owner_id),
) -> None:
    svc = ProjectService(db)
    project = svc.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    _assert_owner(project, owner_id)
    try:
        svc.delete_project(project_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


def _project_progress_snapshot(db: Session, project_id: str) -> tuple[str, int, str | None] | None:
    svc = ProjectService(db)
    project = svc.get_project(project_id)
    if not project:
        return None
    return project.status, project.progress, project.error


@router.get("/{project_id}/events")
async def project_progress_events(project_id: str, db: Session = Depends(get_db)):
    # TODO: auth_enabled 时对 SSE 订阅做 owner 校验
    return progress_event_response("project", project_id, db, load_snapshot=_project_progress_snapshot)
