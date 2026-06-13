# @author zhangzhihao
"""测试公共 fixture。"""

import os

# 必须在导入 app 之前设置，确保测试不依赖真实 API Key
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("LLM_PROVIDER", "mock")
os.environ.setdefault("NOVEL_LLM_PROVIDER", "mock")
os.environ.setdefault("IMAGE_PROVIDER", "mock")
os.environ.setdefault("VIDEO_PROVIDER", "mock")
os.environ.setdefault("COHERENT_MODE", "true")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

import app.models  # noqa: F401 — 注册 ORM 模型
import pytest
from app.core.config import get_settings
from app.core.database import get_db
from app.main import app
from app.models.base import Base
from app.providers.registry import clear_provider_cache
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(autouse=True)
def _mock_m2_services(monkeypatch, request, tmp_path):
    """非 e2e 测试 mock TTS/FFmpeg，避免网络与本地 ffmpeg 依赖。"""
    if request.node.get_closest_marker("e2e"):
        return

    from app.services.tts_service import TTSSynthesisResult

    class FakeTTSService:
        async def synthesize(self, text, output_path, voice=None):
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(b"fake-audio")
            return TTSSynthesisResult(audio_path=output_path, duration=2.0)

    class FakeFFmpegService:
        def compose_shot_clip(
            self,
            video_path,
            audio_path,
            narration_cn,
            output_path,
            target_duration,
            target_width,
            target_height,
        ):
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(b"clip")
            return output_path

        def compose_shot_video_only(
            self,
            video_path,
            narration_cn,
            output_path,
            target_duration,
            target_width,
            target_height,
        ):
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(b"clip-video")
            return output_path

        def probe_duration(self, media_path, fallback=0.0):
            return fallback

        def concat_clips(self, clip_paths, output_path):
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(b"final")
            return output_path

        def extract_last_frame(self, video_path, output_image_path):
            output_image_path.parent.mkdir(parents=True, exist_ok=True)
            output_image_path.write_bytes(b"fake-jpeg")
            return output_image_path

        def concat_clips_xfade(self, clip_paths, output_path, xfade_duration=0.4):
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(b"xfade-video")
            return output_path

        def build_continuous_audio(self, audio_paths, output_path):
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(b"continuous-audio")
            return output_path

        def compose_final_with_continuous_audio(self, video_path, continuous_audio, output_path):
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(b"final")
            return output_path

    monkeypatch.setattr("app.services.generation_service.TTSService", FakeTTSService)
    monkeypatch.setattr("app.services.generation_service.FFmpegService", FakeFFmpegService)
    monkeypatch.setattr(
        "app.services.generation_service._outputs_root",
        lambda: tmp_path / "outputs",
    )

    async def fake_download(url: str, dest):
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(b"fake-video")
        return dest

    monkeypatch.setattr("app.services.generation_service._download_file", fake_download)


@pytest.fixture(autouse=True)
def _novel_chroma_dir(monkeypatch, tmp_path, request):
    """小说测试使用临时 Chroma 目录。"""
    if request.node.get_closest_marker("e2e"):
        yield
        return
    chroma_dir = tmp_path / "chroma"
    monkeypatch.setenv("CHROMA_PERSIST_DIR", str(chroma_dir))
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture(autouse=True)
def _reset_provider_cache():
    get_settings.cache_clear()
    clear_provider_cache()
    yield
    clear_provider_cache()
    get_settings.cache_clear()


@pytest.fixture
def db_engine():
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    from app.core.migrate import run_migrations  # noqa: PLC0415

    run_migrations(engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(db_engine):
    session_factory = sessionmaker(bind=db_engine)
    session = session_factory()
    yield session
    session.close()


@pytest.fixture
def client(db_engine, monkeypatch):
    session_factory = sessionmaker(bind=db_engine)

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    # API、后台任务、lifespan 建表共用同一测试库
    monkeypatch.setattr("app.core.database.engine", db_engine)
    monkeypatch.setattr("app.core.database.SessionLocal", session_factory)
    monkeypatch.setattr("app.services.generation_service.SessionLocal", session_factory)
    monkeypatch.setattr("app.services.novel_generation_service.SessionLocal", session_factory)

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
