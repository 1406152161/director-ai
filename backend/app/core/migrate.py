# @author zhangzhihao
"""启动时数据库迁移：幂等补表/补列，避免要求用户删库。"""

import logging

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

_ASSETS_DDL = """
CREATE TABLE IF NOT EXISTS assets (
    id VARCHAR(36) PRIMARY KEY,
    project_id VARCHAR(36) NOT NULL,
    asset_type VARCHAR(16) NOT NULL,
    asset_key VARCHAR(64) NOT NULL,
    name_cn VARCHAR(128) NOT NULL DEFAULT '',
    description_en TEXT NOT NULL DEFAULT '',
    image_url TEXT,
    status VARCHAR(16) NOT NULL DEFAULT 'pending',
    FOREIGN KEY(project_id) REFERENCES projects(id)
)
"""

_SHOT_COLUMNS: list[tuple[str, str]] = [
    ("character_ids", "TEXT"),
    ("scene_id", "VARCHAR(64)"),
    ("prop_ids", "TEXT"),
]


def run_migrations(engine: Engine) -> None:
    """检查并补全 M3 所需表与列，重复调用安全。"""
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    if "assets" not in tables:
        with engine.begin() as conn:
            conn.execute(text(_ASSETS_DDL))
        logger.info("迁移：已创建 assets 表")

    if "shots" in tables:
        existing = {c["name"] for c in inspector.get_columns("shots")}
        for col_name, col_type in _SHOT_COLUMNS:
            if col_name not in existing:
                with engine.begin() as conn:
                    conn.execute(
                        text(f"ALTER TABLE shots ADD COLUMN {col_name} {col_type}")
                    )
                logger.info("迁移：shots 表已补列 %s", col_name)
