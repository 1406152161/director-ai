# 部署与环境配置

> @author zhangzhihao

## 环境变量文件

| 文件 | 用途 |
|------|------|
| `backend/.env.example` | **后端 SSOT**：Provider、数据库、Agnes、小说线 LLM/Embedding |
| `frontend/.env.example` | 前端 `VITE_API_BASE`（生产必填） |
| 根目录 `.env.example` | 仅索引，指向上述两个文件 |

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env   # 生产或跨域时需要
```

## 本地开发

```bash
# 终端 1 — 后端
cd backend
pip install -r requirements.txt
cp .env.example .env    # mock Provider 即可跑通
uvicorn app.main:app --reload --port 8000

# 终端 2 — 前端
cd frontend
npm install
npm run dev             # http://localhost:5173，/api 代理到 :8000
```

## 生产部署要点

### 前端 `VITE_API_BASE`

构建前在 `frontend/.env` 设置：

```env
VITE_API_BASE=https://api.your-domain.com
```

留空则 API 请求走相对路径 `/api/...`，需 Nginx 等同域反代。

### 后端 Provider（生产清单）

`.env` 中至少配置：

| 能力 | 推荐 |
|------|------|
| 视频 LLM/图/视频 | `LLM_PROVIDER=agnes` 等 + `AGNES_API_KEY` |
| 小说写作 | `NOVEL_LLM_PROVIDER=deepseek` + `DEEPSEEK_API_KEY` |
| 向量记忆 | `NOVEL_EMBEDDING_PROVIDER=auto` + `ZHIPU_API_KEY` |

默认全 `mock` 仅适合本地演示，无法出真片/真 LLM 正文。

**Agnes 视频线生产检查项：**

| 变量 | 说明 |
|------|------|
| `AGNES_API_KEY` | 必填，否则 Provider 初始化失败 |
| `LLM_PROVIDER=agnes` | 脚本/分镜 LLM |
| `IMAGE_PROVIDER=agnes` | 关键帧与资产图 |
| `VIDEO_PROVIDER=agnes` | 镜头视频片段 |
| `TTS_PROVIDER=edge` | 旁白（或后续商用 TTS） |
| `AGNES_VIDEO_TIMEOUT` | 长镜头可适当上调（默认 600s） |
| `COHERENT_MODE=true` | M3 资产一致 + 链式尾帧（推荐） |
| `OUTPUTS_DIR` | 成片目录需持久化卷挂载 |
| `USE_CELERY=true` | 长任务勿用 BackgroundTasks |

联调顺序：先 `curl /api/health?deep=1` 确认 DB/Redis，再创建短视频项目验证 SSE 与成片 URL。

### 数据持久化

| 路径 | 说明 |
|------|------|
| `backend/director_ai.db` | SQLite 业务库（默认） |
| `backend/data/chroma/` | 向量索引（已在 `.gitignore`） |
| `backend/outputs/` | 视频成片与中间产物 |

进程重启后 **BackgroundTasks 任务会丢失**；生产环境请启用 Celery（见下文）。

### Celery 任务队列（生产推荐）

1. 启动 Redis（默认 `6379`）
2. 配置 `backend/.env`：`USE_CELERY=true`
3. 启动 API 与 Worker（两个终端）：

```powershell
cd backend
uvicorn app.main:app --reload --port 8000

# 另开终端
celery -A app.tasks.celery_app worker --loglevel=info --pool=solo
```

Windows 开发建议使用 `--pool=solo`；Linux 生产可用默认 prefork。

| 任务名 | 触发场景 |
|--------|----------|
| `director.run_video_generation` | 创建视频项目 |
| `director.run_novel_generation` | 创建/重试规划 |
| `director.run_novel_start_writing` | 确认规划开写 |
| `director.run_novel_next_chapter` | 续写 |
| `director.run_approve_chapter` | 放行复核章 |
| `director.run_rewrite_chapter` | 重写本章 |
| `director.run_replan_novel` | 手动 replan |
| `POST /api/projects/{id}/retry` | 失败视频项目重试 |

本地/测试默认 `USE_CELERY=false`；生产需 Redis 以支持 **Celery Worker → API SSE** 跨进程进度（`ProgressHub` Redis pub/sub）。

### 实时进度（SSE）

视频进度页与小说工作台通过 Server-Sent Events 订阅状态，无需 2s 轮询：

| 端点 | 说明 |
|------|------|
| `GET /api/projects/{id}/events` | 视频项目进度 |
| `GET /api/novels/{id}/events` | 小说规划/写作进度 |

开发环境下 Vite 已代理 `/api`；生产构建需配置 `VITE_API_BASE` 指向后端根地址。SSE 连接失败时前端自动回退轮询。

### SaaS 鉴权（可选）

默认 `AUTH_ENABLED=false`，本地零门槛。生产多租户：

```env
AUTH_ENABLED=true
JWT_SECRET=<随机长密钥>
```

| 端点 | 说明 |
|------|------|
| `POST /api/auth/register` | 注册（自动创建租户） |
| `POST /api/auth/login` | 登录，返回 JWT |
| `GET /api/auth/me` | 当前用户 |
| `GET /api/auth/status` | 是否启用鉴权 |

启用后创建/列表视频、小说、图文需 `Authorization: Bearer <token>`；数据按 `owner_id` 隔离。

### PostgreSQL（可选，多实例部署）

默认 SQLite 适合单机；多 Worker / 多 API 实例请改用 PostgreSQL：

```env
DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/director_ai
```

```bash
pip install psycopg[binary] alembic
cd backend
alembic upgrade head   # 首次迁移（见 alembic/README.md）
```

`init_db()` 仍会在启动时 `create_all`；Alembic 用于生产 schema 版本管理，与 `app/core/migrate.py` 幂等补列并存。

## 健康检查

```bash
curl http://localhost:8000/api/health
curl "http://localhost:8000/api/health?deep=1"   # DB + Redis 探针
```

## 相关文档

- [execution-plan.md](./execution-plan.md) — 迭代任务
- [backlog-quality.md](./backlog-quality.md) — 质量债
- [architecture.md](./architecture.md) — 架构目标态
