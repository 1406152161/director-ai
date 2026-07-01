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

_NOVELS_DDL = """
CREATE TABLE IF NOT EXISTS novels (
    id VARCHAR(36) PRIMARY KEY,
    premise TEXT NOT NULL,
    genre VARCHAR(32) NOT NULL,
    title VARCHAR(256) NOT NULL DEFAULT '',
    synopsis TEXT NOT NULL DEFAULT '',
    bible_json TEXT NOT NULL DEFAULT '{}',
    status VARCHAR(16) NOT NULL DEFAULT 'pending',
    progress INTEGER NOT NULL DEFAULT 0,
    error TEXT,
    created_at DATETIME
)
"""

_NOVEL_ENTITIES_DDL = """
CREATE TABLE IF NOT EXISTS novel_entities (
    id VARCHAR(36) PRIMARY KEY,
    novel_id VARCHAR(36) NOT NULL,
    entity_type VARCHAR(32) NOT NULL,
    entity_key VARCHAR(64) NOT NULL,
    name VARCHAR(128) NOT NULL DEFAULT '',
    data_json TEXT NOT NULL DEFAULT '{}',
    status VARCHAR(16) NOT NULL DEFAULT 'confirmed',
    last_chapter_index INTEGER NOT NULL DEFAULT 0,
    created_at DATETIME,
    FOREIGN KEY(novel_id) REFERENCES novels(id)
)
"""

_NOVEL_FRAMEWORK_ITEMS_DDL = """
CREATE TABLE IF NOT EXISTS novel_framework_items (
    id VARCHAR(36) PRIMARY KEY,
    novel_id VARCHAR(36) NOT NULL,
    item_type VARCHAR(32) NOT NULL,
    item_key VARCHAR(64) NOT NULL,
    scope VARCHAR(16) NOT NULL DEFAULT 'global',
    chapter_index INTEGER,
    chapter_from INTEGER,
    chapter_to INTEGER,
    title VARCHAR(256) NOT NULL DEFAULT '',
    content TEXT NOT NULL DEFAULT '',
    text_for_embed TEXT NOT NULL DEFAULT '',
    status VARCHAR(16) NOT NULL DEFAULT 'confirmed',
    created_at DATETIME,
    FOREIGN KEY(novel_id) REFERENCES novels(id)
)
"""

_NOVEL_OUTLINE_ITEMS_DDL = """
CREATE TABLE IF NOT EXISTS novel_outline_items (
    id VARCHAR(36) PRIMARY KEY,
    novel_id VARCHAR(36) NOT NULL,
    chapter_index INTEGER NOT NULL,
    title VARCHAR(256) NOT NULL DEFAULT '',
    summary TEXT NOT NULL DEFAULT '',
    hook TEXT NOT NULL DEFAULT '',
    arc_id VARCHAR(64) NOT NULL DEFAULT '',
    volume_id VARCHAR(64) NOT NULL DEFAULT '',
    detail_level VARCHAR(16) NOT NULL DEFAULT 'skeleton',
    locked INTEGER NOT NULL DEFAULT 0,
    created_at DATETIME,
    FOREIGN KEY(novel_id) REFERENCES novels(id),
    UNIQUE(novel_id, chapter_index)
)
"""

_NOVEL_CHAPTERS_DDL = """
CREATE TABLE IF NOT EXISTS novel_chapters (
    id VARCHAR(36) PRIMARY KEY,
    novel_id VARCHAR(36) NOT NULL,
    "index" INTEGER NOT NULL,
    title VARCHAR(256) NOT NULL DEFAULT '',
    content TEXT NOT NULL DEFAULT '',
    summary TEXT NOT NULL DEFAULT '',
    word_count INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(16) NOT NULL DEFAULT 'pending',
    FOREIGN KEY(novel_id) REFERENCES novels(id)
)
"""

_TENANTS_DDL = """
CREATE TABLE IF NOT EXISTS tenants (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(128) NOT NULL DEFAULT '',
    created_at DATETIME
)
"""

_USERS_DDL = """
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    email VARCHAR(256) NOT NULL UNIQUE,
    password_hash VARCHAR(256) NOT NULL DEFAULT '',
    display_name VARCHAR(128) NOT NULL DEFAULT '',
    created_at DATETIME,
    FOREIGN KEY(tenant_id) REFERENCES tenants(id)
)
"""

_ARTICLES_DDL = """
CREATE TABLE IF NOT EXISTS articles (
    id VARCHAR(36) PRIMARY KEY,
    owner_id VARCHAR(36),
    topic TEXT NOT NULL,
    platform VARCHAR(32) NOT NULL DEFAULT 'xiaohongshu',
    tone VARCHAR(32) NOT NULL DEFAULT 'friendly',
    status VARCHAR(16) NOT NULL DEFAULT 'preview',
    title VARCHAR(256) NOT NULL DEFAULT '',
    body_md TEXT NOT NULL DEFAULT '',
    error TEXT,
    created_at DATETIME,
    FOREIGN KEY(owner_id) REFERENCES users(id)
)
"""


def _add_column_if_missing(engine: Engine, table: str, col_name: str, col_type: str) -> None:
    inspector = inspect(engine)
    if table not in inspector.get_table_names():
        return
    existing = {c["name"] for c in inspector.get_columns(table)}
    if col_name not in existing:
        with engine.begin() as conn:
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}"))
        logger.info("迁移：%s 表已补列 %s", table, col_name)


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

    if "novels" not in tables:
        with engine.begin() as conn:
            conn.execute(text(_NOVELS_DDL))
        logger.info("迁移：已创建 novels 表")

    if "novel_chapters" not in tables:
        with engine.begin() as conn:
            conn.execute(text(_NOVEL_CHAPTERS_DDL))
        logger.info("迁移：已创建 novel_chapters 表")

    if "novel_chapters" in tables or "novel_chapters" in set(inspector.get_table_names()):
        inspector = inspect(engine)
        chapter_cols = {c["name"] for c in inspector.get_columns("novel_chapters")}
        for col_name, col_type, default in [
            ("validation_status", "VARCHAR(16)", "pending"),
            ("validation_score", "INTEGER", "0"),
            ("validation_issues", "TEXT", "[]"),
        ]:
            if col_name not in chapter_cols:
                with engine.begin() as conn:
                    conn.execute(
                        text(
                            f"ALTER TABLE novel_chapters ADD COLUMN {col_name} {col_type} "
                            f"NOT NULL DEFAULT '{default}'"
                        )
                    )
                logger.info("迁移：novel_chapters 已补列 %s", col_name)

    tables = set(inspect(engine).get_table_names())
    if "novel_entities" not in tables:
        with engine.begin() as conn:
            conn.execute(text(_NOVEL_ENTITIES_DDL))
        logger.info("迁移：已创建 novel_entities 表")

    if "novel_framework_items" not in tables:
        with engine.begin() as conn:
            conn.execute(text(_NOVEL_FRAMEWORK_ITEMS_DDL))
        logger.info("迁移：已创建 novel_framework_items 表")

    tables = set(inspect(engine).get_table_names())
    if "novel_outline_items" not in tables:
        with engine.begin() as conn:
            conn.execute(text(_NOVEL_OUTLINE_ITEMS_DDL))
        logger.info("迁移：已创建 novel_outline_items 表")

    tables = set(inspect(engine).get_table_names())
    if "tenants" not in tables:
        with engine.begin() as conn:
            conn.execute(text(_TENANTS_DDL))
        logger.info("迁移：已创建 tenants 表")
    if "users" not in tables:
        with engine.begin() as conn:
            conn.execute(text(_USERS_DDL))
        logger.info("迁移：已创建 users 表")
    if "articles" not in tables:
        with engine.begin() as conn:
            conn.execute(text(_ARTICLES_DDL))
        logger.info("迁移：已创建 articles 表")

    _add_column_if_missing(engine, "projects", "owner_id", "VARCHAR(36)")
    _add_column_if_missing(engine, "novels", "owner_id", "VARCHAR(36)")
