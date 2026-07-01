# @author zhangzhihao

Alembic 迁移目录（PostgreSQL 生产可选）。

## 首次使用

```bash
cd backend
pip install alembic psycopg[binary]
# .env 中设置 DATABASE_URL=postgresql+psycopg://...
alembic revision --autogenerate -m "initial"
alembic upgrade head
```

本地 SQLite 仍可用 `init_db()` + `migrate.py` 幂等补列；多实例部署时再切 PostgreSQL + Alembic。
