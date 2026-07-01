# director-ai

AI 导演平台 — 从灵感到成片的工业化创作工作流（Script → Asset → Keyframe → Video），含**短视频**、**长篇小说**与**图文预览**三线。

[![CI](https://github.com/1406152161/director-ai/actions/workflows/ci.yml/badge.svg?branch=dev)](https://github.com/1406152161/director-ai/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

## 功能概览

| 产品线 | 说明 |
|--------|------|
| 视频 | 创意 → 分镜 → 资产 → 图生图 → 视频合成（M3 连贯模式） |
| 小说 | 分层规划（千章级）→ 确认大纲 → 按章写作 → 校验 → 向量记忆续写 |
| 图文 | 多平台图文预览占位（完整生成 Pipeline 待接入） |

## 分支说明

| 分支 | 用途 |
|------|------|
| `main` | 稳定发布 |
| `dev` | 日常开发（**默认工作分支**） |
| `feature/*` | 新功能，合并到 `dev` |

详细流程见 [docs/branch-strategy.md](docs/branch-strategy.md)。

## 快速开始

### 环境要求

| 依赖 | 版本/说明 |
|------|-----------|
| Python | ≥ 3.11 |
| Node.js | 建议 18+（用于前端） |
| FFmpeg | 视频合成**必需**（本地 mock 视频可跑通流程，合成阶段需 FFmpeg） |

### 安装与启动

```bash
git clone https://github.com/1406152161/director-ai.git
cd director-ai
git checkout dev

# 后端 — 复制模板，勿提交真实 .env
cd backend
cp .env.example .env
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 新终端 — 前端
cd frontend
npm install
npm run dev
```

浏览器打开 http://localhost:5173 。

- 默认 Provider 为 **`mock`**，无需 API Key 即可跑通主流程。
- 真实 Key（Agnes、DeepSeek 等）**仅填写在本地 `backend/.env`**，切勿提交仓库。见 [SECURITY.md](SECURITY.md)。

### 可选：Celery + Redis（生产或与线上一致）

```bash
# backend/.env 中 USE_CELERY=true，并启动 Redis 后：
celery -A app.tasks.celery_app worker --loglevel=info --pool=solo
```

## 文档索引

| 文档 | 适合谁 | 内容 |
|------|--------|------|
| **[docs/user-guide.md](docs/user-guide.md)** | 使用者 | 三产品线操作、鉴权、FAQ |
| **[docs/deployment.md](docs/deployment.md)** | 运维 | 环境变量、生产部署、Celery/SSE/鉴权 |
| **[docs/codebase.md](docs/codebase.md)** | 开发者 | 目录结构、模块职责、入口对照 |
| [docs/architecture.md](docs/architecture.md) | 架构 | 分层、Pipeline、路线图 |
| [docs/execution-plan.md](docs/execution-plan.md) | 协作 | 迭代任务与进度 |
| [CHANGELOG.md](CHANGELOG.md) | 所有人 | 版本变更 |

交互式 API 文档：后端启动后访问 http://localhost:8000/docs 。

## 项目结构

```
director-ai/
├── frontend/          # React + TypeScript + Vite
├── backend/           # FastAPI + Pipeline + Celery
├── docs/              # 用户指南、部署、代码说明、设计文档
├── .cursor/rules/     # Agent 三角色协作约定
└── .github/           # CI/CD
```

## 协作规范

- 提交信息：Conventional Commits，建议中文描述
- 贡献流程：[CONTRIBUTING.md](CONTRIBUTING.md)
- GitHub 设置：[docs/github-setup.md](docs/github-setup.md)
- 安全与密钥：[SECURITY.md](SECURITY.md)

## 许可证

[MIT License](LICENSE)
