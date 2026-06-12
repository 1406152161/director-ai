# @author zhangzhihao
"""生成编排集成测试（mock Provider）。"""

import time

import app.models  # noqa: F401
import pytest
from app.models.base import Base
from app.schemas.project import ProjectCreate
from app.services.generation_service import run_generation
from app.services.project_service import ProjectService
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

TEST_DB = "sqlite:///:memory:"


@pytest.fixture
def gen_session_factory():
    engine = create_engine(TEST_DB, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    factory = sessionmaker(bind=engine)
    yield factory
    Base.metadata.drop_all(bind=engine)


@pytest.mark.asyncio
async def test_full_pipeline_pending_to_completed(gen_session_factory, monkeypatch):
    monkeypatch.setattr(
        "app.services.generation_service.SessionLocal", gen_session_factory
    )

    session = gen_session_factory()
    svc = ProjectService(session)
    project = svc.create_project(
        ProjectCreate(story="测试创意", style="anime", duration=15, aspect_ratio="9:16")
    )
    session.close()

    await run_generation(project.id)

    session = gen_session_factory()
    svc = ProjectService(session)
    result = svc.get_project(project.id)
    session.close()
    assert result is not None
    assert result.status == "completed"
    assert result.progress == 100
    assert result.title == "Mock 短片"
    assert len(result.shots) == 2
    for shot in result.shots:
        assert shot.image_url
        assert shot.status == "completed"


@pytest.mark.asyncio
async def test_api_pipeline_with_background(client):
    """通过 API 创建项目并等待后台任务完成。"""
    response = client.post(
        "/api/projects",
        json={
            "story": "一只猫的故事",
            "style": "cinematic",
            "duration": 15,
            "aspect_ratio": "9:16",
        },
    )
    assert response.status_code == 201
    project_id = response.json()["id"]

    # 轮询等待后台任务（TestClient 会在请求结束后执行 BackgroundTasks）
    for _ in range(50):
        detail = client.get(f"/api/projects/{project_id}")
        assert detail.status_code == 200
        data = detail.json()
        if data["status"] in ("completed", "failed"):
            break
        time.sleep(0.1)

    assert data["status"] == "completed"
    assert data["progress"] == 100
    assert len(data["shots"]) >= 1
    assert data["shots"][0]["image_url"]
