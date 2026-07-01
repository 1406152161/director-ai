# 代码结构说明

> @author zhangzhihao

帮助开发者快速定位模块。架构愿景见 [architecture.md](./architecture.md)；任务进度见 [execution-plan.md](./execution-plan.md)。

## 1. 仓库顶层

```
director-ai/
├── frontend/          # React + TS + Vite 工作台
├── backend/           # FastAPI + Pipeline + Celery
├── docs/              # 设计、部署、本指南
├── .cursor/           # Agent 规则与 skills
└── .github/           # CI 工作流
```

---

## 2. 后端 `backend/app/`

### 2.1 入口与配置

| 路径 | 职责 |
|------|------|
| `main.py` | FastAPI 应用、CORS、路由挂载、静态 `/outputs` |
| `core/config.py` | 环境变量 Settings（**读取本地 `.env`，勿提交**） |
| `core/database.py` | SQLAlchemy 引擎与会话 |
| `core/migrate.py` | 启动时幂等补表/补列（SQLite 友好） |
| `core/security.py` | 密码哈希、JWT（鉴权开启时使用） |

### 2.2 API 层 `api/`

| 模块 | 前缀 | 说明 |
|------|------|------|
| `health.py` | `/api/health` | 存活探针；`?deep=1` 检查 DB/Redis |
| `projects.py` | `/api/projects` | 视频项目 CRUD、retry、SSE |
| `novels.py` | `/api/novels` | 小说全流程 API |
| `articles.py` | `/api/articles` | 图文占位 CRUD |
| `auth.py` | `/api/auth` | 注册/登录/me（`AUTH_ENABLED` 时） |
| `streaming.py` | — | SSE `progress_event_response` 封装 |
| `deps.py` | — | JWT 依赖、`owner_id` 注入 |

### 2.3 领域服务 `services/`

**视频线**

| 服务 | 职责 |
|------|------|
| `script_service.py` | LLM 生成分镜 JSON + 资产清单 |
| `asset_service.py` | 角色/场景/道具设定图 |
| `image_service.py` | 分镜关键帧（M3 图生图 + 资产参考） |
| `generation_service.py` | M2/M3 视频 Pipeline 编排 |
| `ffmpeg_service.py` | 单镜合成、xfade 拼接、连续旁白 |
| `tts_service.py` | Edge-TTS 旁白 |
| `project_service.py` | 项目/分镜/资产持久化 |
| `task_dispatch.py` | BackgroundTasks ↔ Celery 统一调度 |
| `progress_hub.py` | 进度广播（内存 + Redis pub/sub） |

**小说线**

| 服务 | 职责 |
|------|------|
| `novel_plan_service.py` | L0/L1/L2 分层规划 |
| `novel_generation_service.py` | 规划/开写/续写/复核编排 |
| `novel_outline_service.py` | 章级大纲 DB（SSOT） |
| `novel_write_service.py` | 单章正文生成 |
| `novel_validate_service.py` | 写后校验 |
| `novel_memory_service.py` | Chroma 向量记忆 |
| `novel_framework_service.py` | 卷弧/伏笔框架检索 |
| `novel_entity_service.py` | 人物/道具实体表 |
| `novel_postwrite_service.py` | 写后 replan、记忆写入 |
| `novel_chat_service.py` | 侧栏改稿对话 |
| `novel_service.py` | 小说 CRUD、导出、Bible |

**其他**

| 服务 | 职责 |
|------|------|
| `auth_service.py` | 用户/租户注册登录 |
| `article_service.py` | 图文占位生成 |

### 2.4 Provider 适配层 `providers/`

策略模式，由 `registry.py` 按 `.env` 中 `*_PROVIDER` 选择实现：

```
providers/
├── llm/       mock | agnes | deepseek | zhipu
├── image/     mock | agnes
├── video/     mock | agnes
├── tts/       mock | edge
└── embedding/ local_hash | zhipu | deepseek | auto
```

**密钥只通过环境变量注入**，代码库内不含真实 Key。

### 2.5 异步任务 `tasks/`

| 文件 | 说明 |
|------|------|
| `celery_app.py` | Celery 实例 |
| `video_tasks.py` | `director.run_video_generation` |
| `novel_tasks.py` | 规划/写作/approve/rewrite/replan |
| `async_runner.py` | 在 Worker 中跑 asyncio |

### 2.6 数据模型 `models/`

| 表 | 模型 |
|----|------|
| 视频 | `Project`, `Shot`, `Asset` |
| 小说 | `Novel`, `NovelChapter`, `NovelOutlineItem`, `NovelEntity`, `NovelFrameworkItem` |
| 图文 | `Article` |
| 鉴权 | `User`, `Tenant` |

### 2.7 小说规划子包 `novel/`

| 文件 | 说明 |
|------|------|
| `plan_constants.py` | L1/L2 batch、初始窗口等常量 |
| `plan_checkpoint.py` | 规划断点续跑 |
| `plan_validate.py` | 规划结果校验 |
| `prompts.py` | 题材与规划 prompt 模板 |

### 2.8 测试 `backend/tests/`

- `conftest.py`：内存 SQLite、mock TTS/FFmpeg、**强制 mock Provider**
- 集成测试覆盖 API、规划、SSE、Celery eager、鉴权等
- `test_e2e.py`：需本地设置 Key 的 e2e（CI 默认跳过，**勿在仓库写 Key**）

### 2.9 数据库迁移

| 方式 | 用途 |
|------|------|
| `init_db()` + `migrate.py` | 本地/SQLite 自动建表补列 |
| `alembic/` | 生产 PostgreSQL 可选版本管理 |

---

## 3. 前端 `frontend/src/`

### 3.1 路由与页面

| 路径 | 组件 | 说明 |
|------|------|------|
| `/` | `HubPage` | 首页、进行中、产品线入口 |
| `/video` | `VideoCreatePage` | 创建视频 |
| `/video/progress/:id` | `ProgressPage` | 进度、分镜、重试 |
| `/novel` | `NovelCreatePage` | 创建小说 |
| `/novel/:id` | `NovelWorkbenchPage` | 工作台 |
| `/article` | `ArticleCreatePage` | 图文创建 |
| `/article/:id` | `ArticlePreviewPage` | 图文预览 |
| `/library` | `LibraryPage` | 作品库 |
| `/login` | `LoginPage` | 鉴权 |

### 3.2 关键模块

| 路径 | 说明 |
|------|------|
| `api/client.ts` | REST 封装；自动附加 Bearer token |
| `hooks/useProgressEvents.ts` | SSE + 断线重连 + 轮询降级 |
| `store/useAuthStore.ts` | 登录态（token 存 localStorage） |
| `store/useAppStore.ts` | 视频创建草稿 |
| `components/` | ProgressBar、StatusBadge、OutlinePanel 等 |
| `utils/` | 状态中文标签、Bible 解析 |

### 3.3 开发代理

`vite.config.ts` 将 `/api`、`/outputs` 代理到 `:8000`；生产构建需 `VITE_API_BASE`。

---

## 4. 三条产品线的代码入口

```
视频：VideoCreatePage → POST /api/projects → task_dispatch
      → generation_service (M3) → project_service

小说：NovelCreatePage → POST /api/novels → novel_generation_service
      → novel_plan_service / novel_write_service / ...

图文：ArticleCreatePage → POST /api/articles → article_service（占位）
```

---

## 5. 配置与环境变量

| 文件 | 是否提交 Git | 说明 |
|------|--------------|------|
| `backend/.env.example` | ✅ 模板 | 变量名与注释，**无真实 Key** |
| `backend/.env` | ❌ 忽略 | 本地/服务器真实配置 |
| `frontend/.env.example` | ✅ 模板 | 仅 `VITE_API_BASE` |
| `frontend/.env` | ❌ 忽略 | 生产 API 地址 |

详见 [deployment.md](./deployment.md) 与 [SECURITY.md](../SECURITY.md)。

---

## 6. 相关文档

| 文档 | 内容 |
|------|------|
| [user-guide.md](./user-guide.md) | 安装后怎么用 |
| [deployment.md](./deployment.md) | 部署与 env 详解 |
| [architecture.md](./architecture.md) | 架构与路线图 |
| [backlog-quality.md](./backlog-quality.md) | 视频质量技术债 |
