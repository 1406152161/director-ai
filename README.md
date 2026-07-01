# director-ai

AI 导演平台 — 从灵感到成片的工业化创作工作流（Script → Asset → Keyframe → Video），含**短视频线**与**长篇小说线**。

[![CI](https://github.com/1406152161/director-ai/actions/workflows/ci.yml/badge.svg?branch=dev)](https://github.com/1406152161/director-ai/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

## 功能概览

| 产品线 | 说明 |
|--------|------|
| 视频 | 创意 → 分镜 → 资产 → 图生图 → 视频合成 |
| 小说 | 分层规划（千章级）→ 确认大纲 → 按章写作 → 质量校验 → 向量记忆续写 |
| 图文 | 敬请期待 |

## 分支说明

| 分支 | 用途 |
|------|------|
| `main` | 稳定发布 |
| `dev` | 日常开发（**默认工作分支**） |
| `feature/*` | 新功能，合并到 `dev` |

详细流程见 [docs/branch-strategy.md](docs/branch-strategy.md)。

## 快速开始

```bash
git clone https://github.com/1406152161/director-ai.git
cd director-ai
git checkout dev

# 后端
cd backend
cp .env.example .env
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 新终端 — 前端
cd frontend
npm install
npm run dev
```

浏览器打开 http://localhost:5173 。默认 Provider 为 `mock`，无需 API Key 即可跑通流程。

**生产部署**见 [docs/deployment.md](docs/deployment.md)（含 `VITE_API_BASE`、Agnes/DeepSeek 配置）。

## 项目结构

```
director-ai/
├── frontend/          # React + TypeScript + Vite
├── backend/           # FastAPI + Pipeline
├── docs/              # 设计文档、execution-plan、deployment
├── .cursor/rules/     # Agent 三角色协作约定
└── .github/           # CI/CD
```

## 文档索引

| 文档 | 内容 |
|------|------|
| [docs/execution-plan.md](docs/execution-plan.md) | 迭代任务与进度 |
| [docs/deployment.md](docs/deployment.md) | 环境变量与部署 |
| [docs/m5-hub-novel-ux-design.md](docs/m5-hub-novel-ux-design.md) | 平台 UX |
| [docs/m6-mega-outline-design.md](docs/m6-mega-outline-design.md) | 千章规划 |
| [CHANGELOG.md](CHANGELOG.md) | 变更记录 |

## 协作规范

- 提交信息：Conventional Commits，建议中文描述
- 贡献流程：[CONTRIBUTING.md](CONTRIBUTING.md)
- GitHub 设置：[docs/github-setup.md](docs/github-setup.md)

## 许可证

[MIT License](LICENSE)
