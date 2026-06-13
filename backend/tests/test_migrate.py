# @author zhangzhihao
"""数据库迁移单元测试。"""

from unittest.mock import MagicMock

import pytest
from app.core.migrate import run_migrations


def test_run_migrations_creates_assets_table():
    engine = MagicMock()
    inspector = MagicMock()
    inspector.get_table_names.return_value = ["projects", "shots"]
    inspector.get_columns.return_value = [
        {"name": "id"},
        {"name": "index"},
    ]

    conn = MagicMock()
    ctx = MagicMock()
    ctx.__enter__ = MagicMock(return_value=conn)
    ctx.__exit__ = MagicMock(return_value=False)
    engine.begin.return_value = ctx

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("app.core.migrate.inspect", lambda _: inspector)
        run_migrations(engine)

    # 应创建 assets 表并补 shots 列
    assert engine.begin.call_count >= 2
    sql_calls = [str(c.args[0]) for c in conn.execute.call_args_list]
    assert any("assets" in s for s in sql_calls)
    assert any("character_ids" in s for s in sql_calls)


def test_run_migrations_idempotent():
    engine = MagicMock()
    inspector = MagicMock()
    inspector.get_table_names.return_value = ["projects", "shots", "assets", "novels", "novel_chapters"]
    inspector.get_columns.return_value = [
        {"name": "id"},
        {"name": "character_ids"},
        {"name": "scene_id"},
        {"name": "prop_ids"},
    ]

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("app.core.migrate.inspect", lambda _: inspector)
        run_migrations(engine)

    engine.begin.assert_not_called()
